"""
WebSocket server that compiles received assets (e.g. shaders) into an Android AssetBundle with
Unity in batchmode and sends the bundle back.

Protocol, one asset per connection:
  client -> server  text message: file name (e.g. "GeneratedShader.shader")
  client -> server  binary message: file content
  server -> client  binary message: the AssetBundle
A failed build closes the connection without sending anything; the Unity log of the build is
written to Logs/bundle_build.log.
"""
import argparse
import asyncio
import os

import websockets

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
BUILD_LOG = os.path.join(PROJECT_PATH, "Logs", "bundle_build.log")

# One Unity instance per project at a time: Unity locks the project, and concurrent requests
# would also clear each other's input and output folders. Created in main(), inside the loop.
build_lock = None


def clear_files(*directories):
    for directory in directories:
        if not os.path.isdir(directory):
            continue
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError as e:
                    print(f"Failed to delete {path}: {e}")


async def build_bundle(args):
    os.makedirs(os.path.dirname(BUILD_LOG), exist_ok=True)
    unity_cmd = [
        args.unity, "-batchmode", "-nographics",
        "-projectPath", PROJECT_PATH,
        "-buildTarget", "Android",
        "-executeMethod", "AssetBundleBuilder.BuildAssetBundlesFromParams",
        "-bundleName", args.bundle_name,
        "-assetPaths", args.asset_save_path,
        "-outputPath", args.bundle_output_path,
        "-logFile", BUILD_LOG,
        "-quit",
    ]
    print("Running Unity build:", " ".join(unity_cmd))
    # Asynchronous, so the server keeps answering pings while Unity runs for a minute or more.
    proc = await asyncio.create_subprocess_exec(*unity_cmd)
    return await proc.wait()


async def handle_client(websocket, args):
    print(f"Connection from {websocket.remote_address}")

    raw_name = await websocket.recv()
    file_bytes = await websocket.recv()
    filename = args.default_name if isinstance(raw_name, bytes) else os.path.basename(raw_name)

    async with build_lock:
        os.makedirs(args.asset_save_path, exist_ok=True)
        os.makedirs(args.bundle_output_path, exist_ok=True)
        clear_files(args.asset_save_path, args.bundle_output_path)

        save_path = os.path.join(args.asset_save_path, filename)
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        print(f"Wrote {len(file_bytes)} bytes to {save_path}")

        returncode = await build_bundle(args)
        bundle_path = os.path.join(args.bundle_output_path, args.bundle_name)
        if returncode != 0 or not os.path.exists(bundle_path):
            print(f"Unity build failed (exit code {returncode}), see {BUILD_LOG}")
            await websocket.close()
            return

        with open(bundle_path, "rb") as f:
            bundle_bytes = f.read()

    await websocket.send(bundle_bytes)
    print(f"Sent {len(bundle_bytes)} bytes: {bundle_path}")
    await websocket.close()


async def main():
    parser = argparse.ArgumentParser(description="Asset WebSocket Server for Unity AssetBundle building")
    parser.add_argument("--ip", default="0.0.0.0",
                        help="IP to listen on (default: 0.0.0.0, all interfaces)")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on (default: 8765)")
    parser.add_argument("--unity", default="Unity",
                        help="Unity editor executable (default: 'Unity' from PATH)")
    parser.add_argument("--asset-save-path", default="Assets/AssetsToBundle",
                        help="Folder the received file is saved to (default: Assets/AssetsToBundle)")
    parser.add_argument("--default-name", default="received.asset",
                        help="File name used when the client sends none (default: received.asset)")
    parser.add_argument("--bundle-output-path", default="Assets/AssetBundles",
                        help="Folder the bundle is built into (default: Assets/AssetBundles)")
    parser.add_argument("--bundle-name", default="mybundle",
                        help="Name of the bundle file (default: mybundle)")
    args = parser.parse_args()

    global build_lock
    build_lock = asyncio.Lock()

    # Relative paths are relative to the Unity project, not to wherever the server was started.
    os.chdir(PROJECT_PATH)

    print(f"Starting WebSocket server on ws://{args.ip}:{args.port}/")
    async with websockets.serve(lambda ws: handle_client(ws, args), args.ip, args.port):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())

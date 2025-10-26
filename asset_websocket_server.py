import asyncio
import websockets
import argparse
import os
import subprocess
import time

def cleanup_files(asset_path, bundle_path, bundle_output_path):
    # Remove asset and bundle files
    for path in [asset_path, bundle_path]:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Deleted old file: {path}")
            except Exception as e:
                print(f"Failed to delete {path}: {e}")
    # Remove all files in the bundle output directory
    if os.path.isdir(bundle_output_path):
        for filename in os.listdir(bundle_output_path):
            file_path = os.path.join(bundle_output_path, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted build file: {file_path}")
                except Exception as e:
                    print(f"Failed to delete build file {file_path}: {e}")

async def handle_client(websocket, args):
    print(f"Connection from {websocket.remote_address}")

    # Ensure needed directories exist
    os.makedirs(args.asset_save_path, exist_ok=True)
    os.makedirs(args.bundle_output_path, exist_ok=True)

    # Clean up before receiving new files
    bundle_path = os.path.join(args.bundle_output_path, args.bundle_name)
    cleanup_files(args.asset_save_path, bundle_path, args.bundle_output_path)

    # Receive asset file name
    raw_name = await websocket.recv()
    if isinstance(raw_name, bytes):
        filename = args.default_name
    else:
        filename = os.path.basename(raw_name)

    save_path = os.path.join(args.asset_save_path, filename)
    print(f"Saving incoming file to {save_path}")

    # Receive asset file bytes
    file_bytes = await websocket.recv()
    with open(save_path, "wb") as f:
        f.write(file_bytes)
    print(f"Wrote {len(file_bytes)} bytes to {save_path}")

    # Build asset bundle using Unity
    unity_cmd = [
        "Unity", "-batchmode", "-nographics",
        "-projectPath", os.getcwd(),
        "-buildTarget", "Android",
        "-executeMethod", "AssetBundleBuilder.BuildAssetBundlesFromParams",
        "-bundleName", args.bundle_name,
        "-assetPaths", args.asset_save_path,
        "-outputPath", args.bundle_output_path,
        "-quit"
    ]
    print("Running Unity build:", ' '.join(unity_cmd))
    proc = subprocess.run(unity_cmd)
    if proc.returncode != 0:
        print("Unity build failed!")
        await websocket.close()
        return

    if os.path.exists(bundle_path):
        with open(bundle_path, "rb") as f:
            bundle_bytes = f.read()
        await websocket.send(bundle_bytes)
        print(f"Bundle sent back to client: {bundle_path}")
    else:
        print(f"Bundle not found: {bundle_path}")
    await websocket.close()


async def main():
    parser = argparse.ArgumentParser(
        description="Asset WebSocket Server for Unity AssetBundle building"
    )
    parser.add_argument(
        '--ip', default='0.0.0.0',
        help='IP to listen on (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port', type=int, default=8765,
        help='Port to listen on (default: 8765)'
    )
    parser.add_argument(
        '--asset-save-path',
        default='Assets/AssetsToBundle',
        help='Directory to save incoming files'
    )
    parser.add_argument(
      '--default-name',
      default='received.asset',
      help='Fallback name if client doesn’t send one'
    )
    parser.add_argument(
        '--bundle-output-path',
        default='Assets/AssetBundles/',
        help='Where to output built bundle'
    )
    parser.add_argument(
        '--bundle-name', default='mybundle',
        help='Name of the bundle file'
    )
    args = parser.parse_args()

    print(f"Starting WebSocket server on ws://{args.ip}:{args.port}/")

    # websockets.serve now calls handler(websocket) only
    async def handler(websocket):
        await handle_client(websocket, args)

    await websockets.serve(handler, args.ip, args.port)
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

# Quest Packager

## Setup

1) Install the correct version of Unity Editor (matching the version of the project where you want to use the asset bundles).
2) Install Python 3.8+ and the `websockets` package:

   ```bash
   pip install websockets
   ```

## Build the Asset Bundles (Headless)

To build asset bundles in headless mode, use the following command:

```bash
Unity -batchmode -nographics -projectPath <PATH_TO_PROJECT> -buildTarget Android -executeMethod AssetBundleBuilder.BuildAssetBundlesFromParams -bundleName <BUNDLE_NAME> -assetPaths <PATH_TO_ASSETS> -outputPath <OUTPUT_PATH> -quit
```

- You can leave out the `-assetPaths` and `-outputPath` parameter to compile all assets in the default folder `Assets/AssetsToBundle/` to the default output path `Assets/AssetBundles/`.

## WebSocket Server for Automated Asset Bundling (Python)

You can run the headless WebSocket server to automate receiving asset files (e.g., shaders, textures, etc.) and sending back compiled asset bundles. The server can be configured via command-line arguments:

**Usage:**

```bash
python asset_websocket_server.py --ip <IP> --port <PORT> --asset-save-path <ASSET_SAVE_PATH> --bundle-output-path <BUNDLE_OUTPUT_PATH> --bundle-name <BUNDLE_NAME>
```

- `--ip` (default: localhost): The IP address to listen on (use `0.0.0.0` to listen on all interfaces).
- `--port` (default: 8765): The port to listen on.
- `--asset-save-path` (default: `Assets/AssetsToBundle/received.asset`): Where to save the incoming asset file.
- `--bundle-output-path` (default: `Assets/AssetBundles`): Where to output the built asset bundle.
- `--bundle-name` (default: `mybundle`): The name of the asset bundle to build and send back.

**Example:**

```bash
python asset_websocket_server.py --ip 0.0.0.0 --port 9000 --asset-save-path "Assets/AssetsToBundle/received.asset" --bundle-output-path "Assets/AssetBundles" --bundle-name mybundle
```

The server will:

1. Wait for a WebSocket connection.
2. Receive an asset file from the client and save it.
3. Trigger Unity in batchmode to build the asset bundle.
4. Send the resulting asset bundle back to the client over the WebSocket connection.

---

**Note:**

- Make sure the Unity Editor executable (`Unity`) is available in your system PATH for the server to launch Unity in batchmode.
- The WebSocket server is a standalone Python application and does not require the Unity Editor to be running.
- You can use any WebSocket client (including Unity on Android/Quest) to send asset files and receive bundles.

# QuestPackager

Compiles assets such as shaders into Android AssetBundles on a PC, so a Meta Quest app can load
content that did not exist when it was built. A small WebSocket server receives a file, builds
the bundle with Unity in batchmode and sends it back.

It is the shader compiler of [ShadAR](https://github.com/teamdarmstadt/ShadAR), which has an LLM
write a shader for a spoken prompt and loads the compiled bundle on the headset at runtime.

## Requirements

- **Unity 6000.3.11f1 with Android Build Support.** A bundle only loads in a player of the same
  Unity version, so this must match the app that loads it (ShadAR uses 6000.3.11f1). The project
  pins the version in `ProjectSettings/ProjectVersion.txt`. Without the Android module the build
  stops with an error instead of producing a bundle the Quest rejects.
- **Python 3.9+** with `websockets`:

  ```bash
  pip install websockets
  ```

- The Unity editor executable on `PATH` as `Unity`, or passed with `--unity`.

The project comes with **OpenXR set to Single Pass Instanced** (`Assets/XR`). Unity only compiles
the stereo shader variants a Single Pass Instanced app needs when the building project has XR
configured; without them, shaders render stretched, mismatched images per eye. Keep this
setting if your app renders in Single Pass Instanced.

## WebSocket server

```bash
python asset_websocket_server.py
```

| Option | Default | |
|---|---|---|
| `--ip` | `0.0.0.0` | Address to listen on (all interfaces) |
| `--port` | `8765` | Port to listen on |
| `--unity` | `Unity` | Unity editor executable |
| `--asset-save-path` | `Assets/AssetsToBundle` | Folder the received file is saved to |
| `--default-name` | `received.asset` | File name used when the client sends none |
| `--bundle-output-path` | `Assets/AssetBundles` | Folder the bundle is built into |
| `--bundle-name` | `mybundle` | Name of the bundle file |

Paths are relative to the project folder. Requests are built one at a time.

**Protocol**, one asset per connection:

1. Client sends a text message with the file name, e.g. `GeneratedShader.shader`.
2. Client sends a binary message with the file content.
3. Server sends the AssetBundle as a binary message and closes the connection.

If the build fails, the server closes the connection without sending anything. Unity's log of
the last build is in `Logs/bundle_build.log`.

## Building bundles by hand

```bash
Unity -batchmode -nographics -projectPath <PATH_TO_PROJECT> -buildTarget Android -executeMethod AssetBundleBuilder.BuildAssetBundlesFromParams -bundleName <BUNDLE_NAME> -assetPaths <PATH1;PATH2> -outputPath <OUTPUT_PATH> -quit
```

Without `-assetPaths` and `-outputPath`, all assets in `Assets/AssetsToBundle/` are built into
`Assets/AssetBundles/`. The bundles are always built for Android, uncompressed. In the editor,
the same build is available under **Build → Build AssetBundles From Parameters**.

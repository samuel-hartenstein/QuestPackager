# Headless Editor Mode

## Setup

1) Install the right version of Unity Editor (matching the version of the project where you want to use the asset bundles).
2) Add the Editor folder to your PATH variable.

## Build the Asset Bundles

to build the asset bundles in headless mode, you can use the following command:

```bash
Unity -batchmode -nographics -projectPath PATH_TO_PROJECT -executeMethod AssetBundleBuilder.BuildAssetBundlesFromParams -bundleName mybundle -assetPaths PATH_TO_ASSETS -outputPath "Build/AssetBundles" -quit
```

Note: You can leave out the assetPaths parameter to compile all assets in the folder `Assets/AssetsToBundle/` as one asset bundle.

The compiled asset bundles will be located in the `Assets\AssetBundles\` directory.

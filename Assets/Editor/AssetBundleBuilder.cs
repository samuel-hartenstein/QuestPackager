using UnityEditor;
using UnityEngine;
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;

public static class AssetBundleBuilder
{
  private const string DefaultAssetsDir = "Assets/AssetsToBundle";
  private const string DefaultOutputDir = "Assets/AssetBundles";

  [MenuItem("Build/Build AssetBundles From Parameters")]
  public static void BuildAssetBundlesFromParams()
  {
    var args = Environment.GetCommandLineArgs();
    string outputPath = GetArg(args, "-outputPath") ?? DefaultOutputDir;
    string bundleName = GetArg(args, "-bundleName");
    string assetsArg = GetArg(args, "-assetPaths");

    if (string.IsNullOrEmpty(assetsArg) && !AssetDatabase.IsValidFolder(DefaultAssetsDir))
    {
      Directory.CreateDirectory(DefaultAssetsDir);
      AssetDatabase.Refresh();
    }

    List<string> assetPathsList = new List<string>();
    if (string.IsNullOrEmpty(assetsArg))
    {
      if (!AssetDatabase.IsValidFolder(DefaultAssetsDir))
      {
        Debug.LogError($"Default assets folder not found: {DefaultAssetsDir}. Provide -assetPaths or create the folder.");
        return;
      }
      var guids = AssetDatabase.FindAssets("", new[] { DefaultAssetsDir });
      assetPathsList = guids
          .Select(AssetDatabase.GUIDToAssetPath)
          .Where(p => !p.EndsWith(".meta", StringComparison.OrdinalIgnoreCase))
          .ToList();
    }
    else
    {
      assetPathsList = assetsArg
          .Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries)
          .Select(p => p.Trim())
          .ToList();
    }

    if (string.IsNullOrEmpty(bundleName) || assetPathsList.Count == 0)
    {
      Debug.LogError("Usage: -bundleName <name> [-assetPaths <path1;path2;...>] [-outputPath <path>].\n" +
                     (string.IsNullOrEmpty(assetsArg)
                      ? $"No assets found in default folder '{DefaultAssetsDir}'."
                      : "No asset paths provided."));
      return;
    }

    foreach (var asset in assetPathsList)
    {
      if (!File.Exists(asset) && !Directory.Exists(asset))
      {
        Debug.LogError($"Asset path not found: {asset}");
        return;
      }
    }

    if (!Directory.Exists(outputPath))
      Directory.CreateDirectory(outputPath);

    var buildMap = new[] {
            new AssetBundleBuild {
                assetBundleName = bundleName,
                assetNames = assetPathsList.ToArray()
            }
        };

    BuildPipeline.BuildAssetBundles(
        outputPath,
        buildMap,
        BuildAssetBundleOptions.UncompressedAssetBundle | BuildAssetBundleOptions.DeterministicAssetBundle,
        EditorUserBuildSettings.activeBuildTarget
    );

    Debug.Log($"AssetBundle '{bundleName}' built with {assetPathsList.Count} assets to: {Path.GetFullPath(outputPath)}");
  }

  private static string GetArg(string[] args, string name)
  {
    for (int i = 0; i < args.Length; i++)
    {
      if (args[i].Equals(name, StringComparison.OrdinalIgnoreCase) && i + 1 < args.Length)
        return args[i + 1];
    }
    return null;
  }
}
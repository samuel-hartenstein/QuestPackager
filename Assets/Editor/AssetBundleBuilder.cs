using UnityEditor;
using UnityEngine;
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;

/// <summary>
/// Builds an Android AssetBundle from command-line parameters (see README). Always targets
/// Android, never the editor's active build target: a machine without the Android module would
/// otherwise build Windows bundles that compile fine and are rejected on the Quest.
/// </summary>
public static class AssetBundleBuilder
{
  private const string DefaultAssetsDir = "Assets/AssetsToBundle";
  private const string DefaultOutputDir = "Assets/AssetBundles";

  [MenuItem("Build/Build AssetBundles From Parameters")]
  public static void BuildAssetBundlesFromParams()
  {
    if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.Android, BuildTarget.Android))
    {
      Fail("The Android Build Support module is not installed for this Unity version.");
      return;
    }

    var args = Environment.GetCommandLineArgs();
    string outputPath = GetArg(args, "-outputPath") ?? DefaultOutputDir;
    string bundleName = GetArg(args, "-bundleName");
    string assetsArg = GetArg(args, "-assetPaths");

    if (string.IsNullOrEmpty(assetsArg) && !AssetDatabase.IsValidFolder(DefaultAssetsDir))
    {
      Directory.CreateDirectory(DefaultAssetsDir);
      AssetDatabase.Refresh();
    }

    List<string> assetPathsList;
    if (string.IsNullOrEmpty(assetsArg))
    {
      assetPathsList = AssetDatabase.FindAssets("", new[] { DefaultAssetsDir })
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
      Fail("Usage: -bundleName <name> [-assetPaths <path1;path2;...>] [-outputPath <path>]. " +
           (string.IsNullOrEmpty(assetsArg)
            ? $"No assets found in default folder '{DefaultAssetsDir}'."
            : "No asset paths provided."));
      return;
    }

    foreach (var asset in assetPathsList)
    {
      if (!File.Exists(asset) && !Directory.Exists(asset))
      {
        Fail($"Asset path not found: {asset}");
        return;
      }
    }

    Directory.CreateDirectory(outputPath);

    var buildMap = new[] {
            new AssetBundleBuild {
                assetBundleName = bundleName,
                assetNames = assetPathsList.ToArray()
            }
        };

    var manifest = BuildPipeline.BuildAssetBundles(
        outputPath,
        buildMap,
        BuildAssetBundleOptions.UncompressedAssetBundle,
        BuildTarget.Android
    );
    if (manifest == null)
    {
      Fail($"Building AssetBundle '{bundleName}' failed; see the errors above.");
      return;
    }

    Debug.Log($"AssetBundle '{bundleName}' built with {assetPathsList.Count} assets to: {Path.GetFullPath(outputPath)}");
  }

  /// <summary>
  /// Logs the error and, in batchmode, exits with a non-zero code: with -quit, a plain return
  /// would end Unity with exit code 0 and the caller could not tell a failed build from a good one.
  /// </summary>
  private static void Fail(string message)
  {
    Debug.LogError(message);
    if (Application.isBatchMode)
    {
      EditorApplication.Exit(1);
    }
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

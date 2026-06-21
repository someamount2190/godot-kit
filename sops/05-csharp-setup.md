# SOP-05 — C# (.NET) game scripts

Godot 4.4 **.NET (Mono)** build + the **.NET 8 SDK** are required for C#. Both
are installed on this box. This whole path is VERIFIED (2026-06-21): a C# scene
built and captured through the GDScript harness.

## Environment (this machine)
- Godot .NET build: the pinned console exe (same as GDScript).
- .NET 8 SDK (per-user, NO admin): `%LOCALAPPDATA%\Microsoft\dotnet` (8.0.422).
  `C:\Program Files\dotnet` has only a runtime — its `sdk\` folder is EMPTY.
- For any dotnet/Godot-C# command, put the per-user dotnet first and set the root:
  ```powershell
  $dotnet="$env:LOCALAPPDATA\Microsoft\dotnet"
  $env:PATH = "$dotnet;" + $env:PATH
  $env:DOTNET_ROOT = $dotnet
  ```

## Gate 1 — project files
`project.godot` must declare the assembly:
```
[dotnet]
project/assembly_name="mygame"
```
A `.csproj` using the Godot SDK:
```xml
<Project Sdk="Godot.NET.Sdk/4.4.0">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <EnableDynamicLoading>true</EnableDynamicLoading>
  </PropertyGroup>
</Project>
```
A C# node script (`partial`, extends a Godot type):
```csharp
using Godot;
public partial class Main : Node2D
{
    public override void _Ready() { /* ... */ }
}
```
Reference it in the `.tscn` exactly like a `.gd`:
`[ext_resource type="Script" path="res://Main.cs" id="1"]`.

## Gate 2 — NuGet source (the gotcha)
`Godot.NET.Sdk` is a NuGet SDK. `dotnet build` fails with
`The SDK 'Godot.NET.Sdk/4.4.0' could not be found` unless it can restore it. The
Godot .NET build SHIPS the packages — point a `nuget.config` (next to the
`.csproj`) at them:
```xml
<configuration>
  <packageSources>
    <add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
    <add key="godot-bundled"
         value="<GODOT_DIR>\GodotSharp\Tools\nupkgs" />
  </packageSources>
</configuration>
```

## Gate 3 — BUILD with the dotnet CLI, not Godot
Do NOT use `godot --build-solutions` — GodotTools' MSBuild path fails here
(`Microsoft.Build.Framework 15.1.0.0 not found`). Build directly:
```powershell
dotnet build path\to\mygame.csproj -c Debug
```
Output: `.godot\mono\temp\bin\Debug\<assembly>.dll`. Confirm RC=0 + the DLL exists.

## Gate 4 — run the loop (SOP-01)
With `DOTNET_ROOT`/PATH set (so Godot's loader finds the runtime), capture the
scene as usual: `run.capture(project, "res://main.tscn", out)`. The GDScript
harness happily instances a C#-scripted scene. VIEW the PNG — a blank/default
frame means `_Ready()` didn't run (assembly not built / not found).

## Gate 5 — rebuild after every C# edit
C# is compiled. Unlike GDScript, a `.cs` change does nothing until you re-run
`dotnet build`. Forgetting this = "my change had no effect." Rebuild, then re-capture.

# LVD Spec

![](https://i.imgur.com/lSP3SRZ.png)

Lets you view lvd files (as long as they can be used with yamlvd) and edit block boundaries for Steve on most stages


## Dependencies
You'll need:
- [ArcExplorer](https://github.com/ScanMountGoat/ArcExplorer), as well as a dump of the `/stage/common/shared/param/` folder
- [Parcel](https://github.com/blu-dev/parcel/releases/tag/v1.0.0) for creating patches of the `groundconfig.prc` file for each of your mods
- [Yamlvd](https://github.com/jam1garner/lvd-rs/releases) to automatically retrieve Camera Boundary info, or StudioSB to find out the boundaries for your stage
- pyyaml (pip install) to read yaml files

## Usage

Don't forget to read the wiki for more detail on how this tool works! Here's a quick start guide:

When booting for the first time, the program will ask you to locate ArcExplorer, Yamlvd and Parcel. This is so we can retrieve the original groundconfig.prc, parse level data, and export the changes you make as a patch file. You'll be greated with a blank canvas, with most of the settings greyed out (as there is no level loaded). Go to File>Load Stage Collision File and select a `.yaml` file to load. If your stage doesn't have a yaml file, you can select a `.lvd` file and this program will run yamlvd for you. If yamlvd doesn't work with this stage (ie Final Destination, WarioWare), you can manually enter data for the camera,blastzone,and stage data.

Edit the Steve LVD Settings values as you see fit. You can also use the Wizard button to automatically set these values. The Wizard will require that your Stage Data values are accurate, so double check to make sure these values make sense.

When you're finished, go to File>Export Patch File. This will create a patch file in whichever mod directory you are currently in under stage/common/shared/param, which makes it instantly ready for your custom stage. This will also save your changes to a prcxml in the workspace folder. The program will read from the prcxml file whenever you load the same yaml file again. If you are working with multiple stages at once for a large stage pack, you can also use Create Workspace Patch. This will create a prcx in the workspace folder with every change you have exported.

# Special Thanks

[jam1garner](https://github.com/jam1garner) - yamlvd program
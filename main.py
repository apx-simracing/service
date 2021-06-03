from json import loads, dumps
from os import listdir, rename, mkdir, unlink, startfile
from os.path import join, exists
from shutil import copytree, copyfile, rmtree, copyfileobj
from subprocess import PIPE, Popen, call
from requests import get
from re import compile, match
from sys import argv
from time import sleep

RFACTOR_PATH = "F:\\Steam\\steamapps\\common\\rFactor 2\\"

WORKSHOP_PATH = "F:\\Steam\\steamapps\\workshop\\content\\365960"

APX_SUFFIX = ".9apx"

RECIEVER = "http://localhost:8080"


def get_subscribed_items() -> list:
    workshop_items = listdir(WORKSHOP_PATH)
    return workshop_items


def check_for_mod_existance(
    prefix: str, component_name: str, component_version: str
) -> bool:
    full_path = join(
        RFACTOR_PATH, "Installed", prefix, component_name, component_version
    )
    return exists(full_path)


def make_baseline():
    # rename existing folders, build empty file structure
    folders = [
        "Manifests",
        "Installed",
    ]

    # backup original folders
    for folder in folders:
        full_path = join(RFACTOR_PATH, folder)
        backup_path = full_path + "_apxbackup"
        if not exists(backup_path):
            rename(full_path, backup_path)

    # create artifical, pseudo-empty folders

    baseline_folders = [
        "Commentary",
        "HUD",
        "Nations",
        "Showroom",
        "Sounds",
        "Talent",
        "UIData",
    ]
    if exists(join(RFACTOR_PATH, "Installed")):
        rmtree(join(RFACTOR_PATH, "Installed"))

    if exists(join(RFACTOR_PATH, "Manifests")):
        rmtree(join(RFACTOR_PATH, "Manifests"))
    for folder in baseline_folders:
        old_path = join(RFACTOR_PATH, "Installed_apxbackup", folder)
        new_path = join(RFACTOR_PATH, "Installed", folder)

        copytree(old_path, new_path)

    # special handling: RFM and default Pace Car
    old_rfm_path = join(
        RFACTOR_PATH, "Installed_apxbackup", "rFm", "All Tracks & Cars_10.mas"
    )
    mkdir(join(RFACTOR_PATH, "Installed", "rFm"))
    rfm_path = join(RFACTOR_PATH, "Installed", "rFm", "All Tracks & Cars_10.mas")

    copyfile(old_rfm_path, rfm_path)

    # pace car create

    pacecar_paths = [
        join(RFACTOR_PATH, "Installed_apxbackup", "Vehicles", "CorvettePC"),
        join(RFACTOR_PATH, "Installed_apxbackup", "Vehicles", "CorvettePCLights"),
    ]

    for path in pacecar_paths:
        new_root_path = join(RFACTOR_PATH, "Installed", "Vehicles")
        if not exists(new_root_path):
            mkdir(new_root_path)
        new_car_path = path.replace("_apxbackup", "")

        copytree(path, new_car_path)

    # create locations

    mkdir(join(RFACTOR_PATH, "Installed", "Locations"))

    # create manifests
    mkdir(join(RFACTOR_PATH, "Manifests"))
    manifest_file = join(
        RFACTOR_PATH, "Manifests_apxbackup", "all tracks & cars_10.mft"
    )
    manifest_target_file = manifest_file.replace("_apxbackup", "")
    copyfile(manifest_file, manifest_target_file)


def mod_mgr_install(path: str, component_name: str, component_version: str):
    mod_mgr_path = join(RFACTOR_PATH, "Bin64", "ModMgr.exe")
    cmd_line = [
        mod_mgr_path,
        f"-c{RFACTOR_PATH}",
        "-q",
        f"-i{path}",
    ]
    build = Popen(
        cmd_line,
        shell=True,
        stdout=PIPE,
        stderr=PIPE,
    ).wait()


def install_mods(mod: dict) -> bool:
    if "cars" not in mod or "track" not in mod:
        return False

    cars = mod["cars"]
    track = mod["track"]

    for workshop_id, car in cars.items():
        workshop_path = join(WORKSHOP_PATH, workshop_id)
        if "-" not in str(workshop_id):
            component = car["component"]["name"]
            version = car["component"]["version"]

            # at this point, we only care about base version, not mods
            if APX_SUFFIX in version:
                version = version.replace(APX_SUFFIX, "")

            if exists(workshop_path):
                files = listdir(workshop_path)
                for file in files:
                    full_mod_path = join(workshop_path, file)
                    mod_mgr_install(full_mod_path, component, version)
                if not check_for_mod_existance("Vehicles", component, version):
                    raise Exception(
                        "Installation failed",
                        component,
                        version,
                    )
                else:
                    print("Component ", component, version, " was installed")
            else:
                print("Workshop missing")
        else:
            print("file based items not supported")

    for workshop_id, track_item in track.items():
        workshop_path = join(WORKSHOP_PATH, workshop_id)
        if "-" not in str(workshop_id):
            component = track_item["component"]["name"]
            version = track_item["component"]["version"]

            # at this point, we only care about base version, not mods
            if APX_SUFFIX in version:
                version = version.replace(APX_SUFFIX, "")

            if exists(workshop_path):
                files = listdir(workshop_path)
                for file in files:
                    full_mod_path = join(workshop_path, file)
                    mod_mgr_install(full_mod_path, component, version)
                if not check_for_mod_existance("Locations", component, version):
                    raise Exception(
                        "Installation failed",
                        component,
                        version,
                    )
                else:
                    print("Component ", component, version, " was installed")
            else:
                print("Workshop missing")
        else:
            print("file based items not supported")


def print_brand():
    print("           _______   __")
    print("     /\   |  __ \ \ / /")
    print("    /  \  | |__) \ V / ")
    print("   / /\ \ |  ___/ > <  ")
    print("  / ____ \| |    / . \ ")
    print(" /_/    \\_\\_|   /_/ \\_\\")
    print("")
    print("Client side service worker - apx.chmr.eu")


def apply_updates(target: str, mod: dict) -> bool:
    if "cars" not in mod or "track" not in mod:
        return False
    cars = mod["cars"]
    track = mod["track"]

    for steamid, car in cars.items():
        component = car["component"]["name"]
        version = car["component"]["version"]
        update = car["component"]["update"]
        if not update:
            print("\tIgnoring {component} {version} as it's no update")
        if update:
            print("\t🎁 " + component, version, "is an update.")
            if APX_SUFFIX in version:
                print("\t✅ Update build with APX")
                parent = join(
                    RFACTOR_PATH,
                    "Installed",
                    "Vehicles",
                    component,
                    version.replace(APX_SUFFIX, ""),
                )
                if exists(parent):
                    print(
                        f"\t✅ Parent component {component} "
                        + version.replace(APX_SUFFIX, "")
                        + " is installed"
                    )
                else:
                    print("\t❌ Parent is NOT existing")
                    suspected_path = join(WORKSHOP_PATH, steamid)
                    if exists(suspected_path):
                        print("\t🛠 Found workshop content")
                        files = listdir(suspected_path)
                        for file in files:
                            full_mod_path = join(suspected_path, file)
                            mod_mgr_install(full_mod_path, component, version)
                    if not check_for_mod_existance(
                        "Vehicles", component, version.replace(APX_SUFFIX, "")
                    ):
                        if "-" not in str(steamid):
                            raise Exception(
                                f"The mod base cannot be installed. Check https://steamcommunity.com/sharedfiles/filedetails/?id={steamid}"
                            )
                        else:
                            raise Exception(
                                f"The mod base cannot be installed. Check the mod source."
                            )

            target = f"{target}/files/{component}/{version}"
            files = get(target).json()

            print(
                "\t✅",
                component,
                version,
                "consists out of " + str(len(files)) + " files.",
            )
            root_path = join(RFACTOR_PATH, "Installed", "Vehicles", component, version)
            if exists(root_path):
                rmtree(root_path)
                print(
                    "\t✅",
                    component,
                    version,
                    "was already existing. Forcing update with overwrite.",
                )
            if not exists(root_path):
                mkdir(root_path)
            for file in files:
                r = get(target + "/" + file, stream=True)
                if r.status_code == 200:
                    file_path = join(root_path, file)
                    with open(file_path, "wb") as f:
                        r.raw.decode_content = True
                        copyfileobj(r.raw, f)
                        print(f"\t✅ Placed {file} for component {component} {version}")


def remove_updates(mod: dict) -> bool:
    if "cars" not in mod or "track" not in mod:
        return False
    cars = mod["cars"]
    track = mod["track"]

    for _, car in cars.items():
        component = car["component"]["name"]
        version = car["component"]["version"]
        update = car["component"]["update"]
        if update:
            root_path = join(RFACTOR_PATH, "Installed", "Vehicles", component, version)
            if exists(root_path):
                rmtree(root_path)
                print("\t🚮 ", component, version, "removed")
            else:
                print("\t❌ ", component, version, "not installed")


def connect(target):

    print(f"🔎 Attempting connect towards {target}")
    got = get(f"{target}/mod").json()
    mod_path = join(RFACTOR_PATH, "apx.json")
    do_nothing = False
    if exists(mod_path):
        print(
            f"🔎 Previous connection found. Investigating if same mod, removing if needed"
        )
        with open(mod_path, "r") as file:
            content = loads(file.read())
            name = content["mod"]["mod"]["name"]
            version = content["mod"]["mod"]["version"]

            new_name = got["mod"]["mod"]["name"]
            new_version = got["mod"]["mod"]["version"]

            if name == new_name and version == new_version:
                print(f"🔎 Mod is identical. Doing nothing.")
                do_nothing = True
            else:
                # remove_updates(content["mod"])
                # remove manifest and rfm
                path = join(
                    RFACTOR_PATH,
                    "Manifests",
                    name + "_" + version.replace(".", "") + ".mft",
                )
                if exists(path):
                    unlink(path)
                    print("\t🚮 Removed manifests", path)
                rfm_path = join(
                    RFACTOR_PATH,
                    "Installed",
                    "rFm",
                    name + "_" + version.replace(".", "") + ".mas",
                )

                if exists(rfm_path):
                    unlink(rfm_path)
                    print("\t🚮 Removed rFm package", rfm_path)
    if not do_nothing:
        with open(mod_path, "w") as file:
            file.write(dumps(got))
        print(f"✅ Recieved mod contents")
        if "mod" in got and "comp" in got["mod"]:
            print(f"✅ Found APX version", got["mod"]["comp"])
        apply_updates(target, got["mod"])
    pattern = r"https?://([^\:]+)"
    taget_match = match(pattern, target)
    if taget_match:
        sim_target = taget_match.groups(1)[0] + ":" + str(got["port"])
        command_line = f"steam://run/365960//+connect={sim_target}"
        print(f"🚀 Launching: {command_line}")
        startfile(command_line)


if __name__ == "__main__":
    if len(argv) > 1:
        print_brand()
        connect(argv[1])

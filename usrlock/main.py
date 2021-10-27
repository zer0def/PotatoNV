import sys
import argparse
import json
import hashlib
from os import path
from glob import glob
from ui import *

from lxml import etree

try:
    from imageflasher import *
    from fastboot import *
except Exception as e:
    error("Failed to import some dependencies.")
    error(str(e))
    tip("Install dependencies with pip:", "python3.%d -m pip install -r requirements.txt" % sys.version_info[1])
    exit(1)


def setup():
    parser = argparse.ArgumentParser(epilog="""Copyright 2020 mashed-potatoes
Copyright 2019 Penn Mackintosh
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.""")
    parser.add_argument("--skip-bootloader", "-s", action="store_true",
        help="Skip bootloader flashing")
    parser.add_argument("--key", "-k", help="What key should be set?",
        required=True)
    parser.add_argument("--fblock", "-f", action="store_true",
        help="Set FBLOCK to False")
    parser.add_argument("--bootloader", "-b", help="Specify bootloader name")
    parser.add_argument("--restart", "-r", action="store_true",
        help="Reboot after flashing")
    args = parser.parse_args()

    if len(args.key) != 16:
        error("Invalid key length!", critical=True)
    if not args.skip_bootloader and not args.bootloader:
        error("Bootloader specification missing!", critical=True)

    return args


def flash_images(data: dict):
    flasher = ImageFlasher()
    flasher.connect_serial()
    for image in data.get("images", []):
        progress(title="Flashing {}".format(image['role']))
        flasher.download_from_disk(
            "./bootloaders/{}/{}".format(data['name'], image['filename']),
            int(image['address'], 16)
        )
    success("Bootloader uploaded.")


def write_nvme(key: str, fblock: bool, reboot: bool):
    info("Waiting for device...")
    m = hashlib.sha256()
    m.update(key.encode())
    fb = Fastboot()
    info("Connecting to fastboot device...")
    fb.connect()
    fb.write_nvme(b"USRKEY", m.digest())
    success("Bootloader code updated")
    if fblock:
        fb.write_nvme(b"FBLOCK", b'\0')
        success("FBLOCK set to 0")
    if reboot:
        info("Rebooting device...")
        fb.reboot()


def parse_manifest(btldr: str):
    if path.isfile("./bootloaders/{}/manifest.json".format(btldr)):
        payload = json.load(open("./bootloaders/{}/manifest.json".format(btldr)))
        payload["name"] = btldr
        return payload

    if path.isfile("./bootloaders/{}/manifest.xml".format(btldr)):
        xml = etree.parse(open("./bootloaders/{}/manifest.xml".format(btldr)))
        return {
            "name": btldr,
            "images": [{
                "filename": i.get("path"),
                "role": i.get("role"),
                "address": i.get("address"),
                #"hash": i.get("hash")
            } for i in xml.xpath("/bootloader/image")],
            "props": {}
        }

    return {}


def main():
    args = setup()
    if not args.skip_bootloader:
        flash_images(parse_manifest(args.bootloader))
    write_nvme(args.key, args.fblock, args.restart)


if __name__ == '__main__':
    main()

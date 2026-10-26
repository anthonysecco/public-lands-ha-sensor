"""Forest Service forest code -> short name used in fs.usda.gov links.

Built from the Forest Service recreation layer (EDW_RecreationOpportunities_01).
Links use https://www.fs.usda.gov/<name>, which the Forest Service redirects to
the forest's current page. Checked weekly by scripts/check_links.py.
"""

FOREST_SLUGS: dict[str, str] = {
    "0102": "bdnf",  # Beaverhead-Deerlodge National Forest
    "0103": "bitterroot",  # Bitterroot National Forest
    "0104": "ipnf",  # Idaho Panhandle National Forests
    "0110": "flathead",  # Flathead National Forest
    "0111": "custergallatin",  # Custer Gallatin National Forest
    "0112": "hlcnf",  # Helena-Lewis and Clark National Forest
    "0114": "kootenai",  # Kootenai National Forest
    "0116": "lolo",  # Lolo National Forest
    "0117": "nezperceclearwater",  # Nez Perce-Clearwater National Forests
    "0118": "dpg",  # Dakota Prairie Grasslands
    "0202": "bighorn",  # Bighorn National Forest
    "0203": "blackhills",  # Black Hills National Forest
    "0204": "gmug",  # Grand Mesa, Uncompahgre and Gunnison National Fore
    "0206": "mbr",  # Medicine Bow-Routt NFs and Thunder Basin NG
    "0207": "nebraska",  # Nebraska National Forests and Grasslands
    "0209": "riogrande",  # Rio Grande National Forest
    "0210": "arp",  # Arapaho & Roosevelt National Forests Pawnee NG
    "0212": "psicc",  # Pike-San Isabel National Forests
    "0213": "sanjuan",  # San Juan National Forest
    "0214": "shoshone",  # Shoshone National Forest
    "0215": "whiteriver",  # White River National Forest
    "0301": "asnf",  # Apache-Sitgreaves National Forest
    "0302": "carson",  # Carson National Forest
    "0303": "cibola",  # Cibola National Forest and Grasslands
    "0304": "coconino",  # Coconino National Forest Recreation
    "0305": "coronado",  # Coronado National Forest
    "0306": "gila",  # Gila National Forest
    "0307": "kaibab",  # Kaibab National Forest
    "0308": "lincoln",  # Lincoln National Forest
    "0309": "prescott",  # Prescott National Forest
    "0310": "santafe",  # Santa Fe National Forest
    "0312": "tonto",  # Tonto National Forest
    "0401": "ashley",  # Ashley National Forest
    "0402": "boise",  # Boise National Forest
    "0403": "btnf",  # Bridger-Teton National Forest
    "0407": "dixie",  # Dixie National Forest
    "0408": "fishlake",  # Fishlake National Forest
    "0410": "mantilasal",  # Manti-La Sal National Forest
    "0412": "payette",  # Payette National Forest
    "0413": "scnf",  # Salmon-Challis National Forest
    "0414": "sawtooth",  # Sawtooth National Forest
    "0415": "ctnf",  # Caribou-Targhee National Forest
    "0417": "htnf",  # Humboldt-Toiyabe National Forest
    "0419": "uwcnf",  # Uinta-Wasatch-Cache National Forest
    "0501": "angeles",  # Angeles National Forest
    "0502": "cleveland",  # Cleveland National Forest
    "0503": "eldorado",  # Eldorado National Forest
    "0504": "inyo",  # Inyo National Forest
    "0505": "klamath",  # Klamath National Forest
    "0506": "lassen",  # Lassen National Forest
    "0507": "lpnf",  # Los Padres National Forest
    "0508": "mendocino",  # Mendocino National Forest
    "0509": "modoc",  # Modoc National Forest
    "0510": "srnf",  # Six Rivers National Forest
    "0511": "plumas",  # Plumas National Forest
    "0512": "sbnf",  # San Bernardino National Forest
    "0513": "sequoia",  # Sequoia National Forest
    "0514": "stnf",  # Shasta-Trinity National Forest
    "0515": "sierra",  # Sierra National Forest
    "0516": "stanislaus",  # Stanislaus National Forest
    "0517": "tahoe",  # Tahoe National Forest
    "0519": "ltbmu",  # Lake Tahoe Basin Management Unit
    "0601": "deschutes",  # Deschutes National Forest
    "0602": "fremont-winema",  # Fremont-Winema National Forest
    "0603": "giffordpinchot",  # Gifford Pinchot National Forest
    "0604": "malheur",  # Malheur National Forest
    "0605": "mbs",  # Mt. Baker-Snoqualmie National Forest
    "0606": "mthood",  # Mt. Hood National Forest
    "0607": "ochoco",  # Ochoco National Forest
    "0609": "olympic",  # Olympic National Forest
    "0610": "rogue-siskiyou",  # Rogue River-Siskiyou National Forest
    "0612": "siuslaw",  # Siuslaw National Forest
    "0614": "umatilla",  # Umatilla National Forest
    "0615": "umpqua",  # Umpqua National Forest
    "0616": "wallowa-whitman",  # Wallowa Whitman National Forest
    "0617": "okawen",  # Okanogan-Wenatchee National Forest
    "0618": "willamette",  # Willamette National Forest
    "0621": "colville",  # Colville National Forest
    "0622": "crgnsa",  # Columbia River Gorge National Scenic Area
    "0801": "alabama",  # National Forests in Alabama
    "0802": "dbnf",  # Daniel Boone National Forest
    "0803": "conf",  # Chattahoochee-Oconee National Forest
    "0804": "cherokee",  # Cherokee National Forest
    "0806": "kisatchie",  # Kisatchie National Forest
    "0807": "mississippi",  # National Forests in Mississippi
    "0808": "gwj",  # George Washington & Jefferson National Forest
    "0809": "ouachita",  # Ouachita National Forest
    "0810": "osfnf",  # Ozark-St. Francis National Forests
    "0811": "nfsnc",  # National Forests in North Carolina
    "0812": "scnfs",  # Francis Marion and Sumter National Forests
    "0813": "texas",  # National Forests and Grasslands in Texas
    "0818": "florida",  # National Forests in Florida
    "0819": "elyunque",  # El Yunque National Forest
    "0903": "chippewa",  # Chippewa National Forest
    "0904": "hmnf",  # Huron-Manistee National Forests
    "0905": "mtnf",  # Mark Twain National Forest
    "0907": "ottawa",  # Ottawa National Forest
    "0908": "shawnee",  # Shawnee National Forest
    "0909": "superior",  # Superior National Forest
    "0910": "hiawatha",  # Hiawatha National Forest
    "0912": "hoosier",  # Hoosier National Forest
    "0913": "cnnf",  # Chequamegon-Nicolet NF
    "0914": "wayne",  # Wayne National Forest
    "0915": "midewin",  # Midewin National Tallgrass Prairie
    "0919": "allegheny",  # Allegheny National Forest
    "0920": "gmfl",  # Green Mountain & Finger Lakes National Forests
    "0921": "mnf",  # Monongahela National Forest
    "0922": "whitemountain",  # White Mountain National Forest
    "1004": "chugach",  # Chugach National Forest
    "1005": "tongass",  # Tongass National Forest
}

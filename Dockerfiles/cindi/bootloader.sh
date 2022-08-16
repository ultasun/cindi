#!/bin/sh
# thanks to Pranav Malvawala for the intuitive shell script
# https://pranavmalvawala.com/run-script-only-on-first-start-up

# beginning of file bootloader.sh
# ------------------------------------------------------------------------------
# begin function definitions

show_license() {
    echo ""
    cat ./LICENSE
    echo ""
}

first_boot() {
    python ./sqlite3_initialization_helper.py
}

normal_boot() {
    python ./app.py
}

# end function definitions 
# ------------------------------------------------------------------------------
# begin script execution area 
cd /app
show_license

FIRST_BOOT_RECORD="./logs/CINDI_FIRST_BOOT"
if [ ! -e ./$FIRST_BOOT_RECORD ]; then
    mkdir -p ./logs
    echo `date` > $FIRST_BOOT_RECORD
    first_boot
fi

# start the application normally
normal_boot

# end script execution area
# ------------------------------------------------------------------------------
# end of file bootloader.sh

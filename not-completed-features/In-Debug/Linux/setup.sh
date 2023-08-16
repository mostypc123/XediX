#!/bin/bash

app_name=""
download_url=""
platform=""

while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
        --source)
            platform="source"
            shift
            ;;
        --win)
            platform="windows"
            shift
            ;;
        --linux)
            platform="linux"
            shift
            ;;
        --mac)                  # Pridaný prípad pre macOS
            platform="mac"
            shift
            ;;
        *)
            app_name="$1"
            shift
            ;;
    esac
done

if [ "$app_name" = "xedix" ]; then
    if [ "$platform" = "source" ]; then
        download_url="URL_OF_XEDIX_SOURCE_CODE"
        echo "Downloading xedix source code."
    elif [ "$platform" = "windows" ]; then
        download_url="URL_OF_XEDIX_WINDOWS"
        echo "Downloading xedix for Windows."
    elif [ "$platform" = "linux" ]; then
        download_url="URL_OF_XEDIX_LINUX"
        echo "Downloading xedix for Linux."
    elif [ "$platform" = "mac" ]; then
        download_url="URL_OF_XEDIX_MAC"
        echo "Downloading xedix for macOS."
    else
        echo "Missing or invalid platform argument. Use --source, --win, --linux, or --mac."
    fi

    if [ "$download_url" != "" ]; then
        wget "$download_url" -O xedix.zip
        echo "xedix app downloaded."
    fi
elif [ "$app_name" = "xnotex" ]; then
    # Podobná logika pre xnotex aplikáciu
    # ...
else
    echo "Invalid app name. Use 'xedix' or 'xnotex'."
fi

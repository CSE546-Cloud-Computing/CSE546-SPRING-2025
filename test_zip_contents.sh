#!/bin/bash

# Zip format compliance
TOTAL_FILES=0
TOTAL_DIRS=0
EXTRA_FILES=""

MODULE_ERR=""
KERNEL_MODULE_MSG=""

check_file ()
{
    local file_name=$(realpath "$1" 2>/dev/null)

    if [ -e ${file_name} ]; then
        let TOTAL_FILES=TOTAL_FILES+1
        echo "[log]: - file ${file_name} found"
        return 0
    else
        return 1
    fi
}

check_dir ()
{
    local dir_name=$(realpath "$1" 2>/dev/null)

    if [ -d ${dir_name} ]; then
        let TOTAL_DIRS=TOTAL_DIRS+1
        echo "[log]: - directory ${dir_name} found"
        return 0
    else
        return 1
    fi
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

check_zip_content ()
{
    # Step 1: Check for `credentials` directory - stop if failed
    echo "[log]: Look for credentials directory (credentials)"
    if ! check_dir "credentials"; then
        MODULE_ERR="${MODULE_ERR}"
        return 1
    fi

    # Step 2: Check credentials.txt - stop if failed
    echo "[log]: Look for credentials.txt"
    if ! check_file "credentials/credentials.txt"; then
        MODULE_ERR="${MODULE_ERR}"
        return 1
    fi

    return 0
}

run_zip_test ()
{
    local zip_file=$(realpath "$1")
    local unzip_dir="unzip_$(date +%s)"

    mkdir -p ${unzip_dir}
    pushd ${unzip_dir} 1>/dev/null

    unzip ${zip_file} 1>/dev/null
    if check_zip_content; then
        echo -e "[test_zip_contents]: Passed"
    else
        echo -e "[test_zip_contents]: Failed. Please read the document carefully."
    fi

    popd 1>/dev/null
    rm -rf ${unzip_dir}
}

if [ "$#" -ne 1 ]; then
    echo "Usage: ./test_zip_contents.sh </path/to/your/submission.zip>"
    exit 1
fi

if [ -e "$1" ]; then
    run_zip_test "$1"
else
    echo "File $1 does not exist"
    exit 1
fi

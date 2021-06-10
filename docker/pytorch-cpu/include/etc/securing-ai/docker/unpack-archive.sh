#!/bin/bash
# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.

# Created by argbash-init v2.8.1
# ARG_OPTIONAL_BOOLEAN([delete],[d],[Delete archive file after unpacking])
# ARG_POSITIONAL_SINGLE([archive-filepath],[Path to a tarball or zip archive],[])
# ARG_DEFAULTS_POS()
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Unpack archive in current directory\n])"
# ARGBASH_GO()
# needed because of Argbash --> m4_ignore([
### START OF CODE GENERATED BY Argbash v2.10.0 one line above ###
# Argbash is a bash code generator used to get arguments parsing right.
# Argbash is FREE SOFTWARE, see https://argbash.io for more info


die()
{
  local _ret="${2:-1}"
  test "${_PRINT_HELP:-no}" = yes && print_help >&2
  echo "$1" >&2
  exit "${_ret}"
}


begins_with_short_option()
{
  local first_option all_short_options='dh'
  first_option="${1:0:1}"
  test "$all_short_options" = "${all_short_options/$first_option/}" && return 1 || return 0
}

# THE DEFAULTS INITIALIZATION - POSITIONALS
_positionals=()
_arg_archive_filepath=
# THE DEFAULTS INITIALIZATION - OPTIONALS
_arg_delete="off"


print_help()
{
  printf '%s\n' "Unpack archive in current directory
"
  printf 'Usage: %s [-d|--(no-)delete] [-h|--help] <archive-filepath>\n' "$0"
  printf '\t%s\n' "<archive-filepath>: Path to a tarball or zip archive"
  printf '\t%s\n' "-d, --delete, --no-delete: Delete archive file after unpacking (off by default)"
  printf '\t%s\n' "-h, --help: Prints help"
}


parse_commandline()
{
  _positionals_count=0
  while test $# -gt 0
  do
    _key="$1"
    case "$_key" in
      -d|--no-delete|--delete)
        _arg_delete="on"
        test "${1:0:5}" = "--no-" && _arg_delete="off"
        ;;
      -d*)
        _arg_delete="on"
        _next="${_key##-d}"
        if test -n "$_next" -a "$_next" != "$_key"
        then
          { begins_with_short_option "$_next" && shift && set -- "-d" "-${_next}" "$@"; } || die "The short option '$_key' can't be decomposed to ${_key:0:2} and -${_key:2}, because ${_key:0:2} doesn't accept value and '-${_key:2:1}' doesn't correspond to a short option."
        fi
        ;;
      -h|--help)
        print_help
        exit 0
        ;;
      -h*)
        print_help
        exit 0
        ;;
      *)
        _last_positional="$1"
        _positionals+=("$_last_positional")
        _positionals_count=$((_positionals_count + 1))
        ;;
    esac
    shift
  done
}


handle_passed_args_count()
{
  local _required_args_string="'archive-filepath'"
  test "${_positionals_count}" -ge 1 || _PRINT_HELP=yes die "FATAL ERROR: Not enough positional arguments - we require exactly 1 (namely: $_required_args_string), but got only ${_positionals_count}." 1
  test "${_positionals_count}" -le 1 || _PRINT_HELP=yes die "FATAL ERROR: There were spurious positional arguments --- we expect exactly 1 (namely: $_required_args_string), but got ${_positionals_count} (the last one was: '${_last_positional}')." 1
}


assign_positional_args()
{
  local _positional_name _shift_for=$1
  _positional_names="_arg_archive_filepath "

  shift "$_shift_for"
  for _positional_name in ${_positional_names}
  do
    test $# -gt 0 || break
    eval "$_positional_name=\${1}" || die "Error during argument parsing, possibly an Argbash bug." 1
    shift
  done
}

parse_commandline "$@"
handle_passed_args_count
assign_positional_args 1 "${_positionals[@]}"

# OTHER STUFF GENERATED BY Argbash

### END OF CODE GENERATED BY Argbash (sortof) ### ])
# [ <-- needed because of Argbash

shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly archive_filepath="${_arg_archive_filepath}"
readonly bool_delete="${_arg_delete}"
readonly logname="Unpack Archive"

###########################################################################################
# Unpack tarball archive
#
# Globals:
#   logname
# Arguments:
#   Tarball, a path
# Returns:
#   None
###########################################################################################

untar_file() {
  local archive_dir="$(dirname $1)"
  local archive_file="$(basename $1)"

  echo "${logname}: untar ${archive_file} into ${archive_dir}"

  bash -c "cd ${archive_dir} && tar xf ${archive_file}"
}

###########################################################################################
# Unpack zip archive
#
# Globals:
#   logname
# Arguments:
#   Zip archive, a path
# Returns:
#   None
###########################################################################################

unzip_file() {
  local archive_dir="$(dirname $1)"
  local archive_file="$(basename $1)"

  echo "${logname}: unzip ${archive_file} into ${archive_dir}"

  bash -c "cd ${archive_dir} && unzip ${archive_file}"
}

###########################################################################################
# Unpack an archive
#
# Globals:
#   archive_filepath
#   bool_delete
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

unpack_archive() {
  case ${archive_filepath} in
    *.tar | *.tar.bz2 | *.tar.gz | *.tar.xz | *.tgz)
      untar_file ${archive_filepath}
      if [[ ${bool_delete} == on ]]; then
        rm ${archive_filepath}
      fi
      ;;
    *.zip)
      unzip_file ${archive_filepath}
      if [[ ${bool_delete} == on ]]; then
        rm ${archive_filepath}
      fi
      ;;
    *)
      echo "${logname}: WARNING - unsupported file format - $(basename ${archive_filepath})" 1>&2
      ;;
  esac
}

###########################################################################################
# Main script
###########################################################################################

unpack_archive
# ] <-- needed because of Argbash

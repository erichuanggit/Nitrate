#!/bin/bash
usage()
{
cat <<EOF
usage: $0 options
WARNING! This script will drop Nitrate legacy tables from a MySQL database
OPTIONS:
    -u      Database username
    -d      Database/schema name
    -h      Host name (optional)
    -p      Port (optional)
EOF
}
USERNAME=
DBSCHEMA=
HOST=
PORT=

# Read options from command line
while getopts "u:d:h:p" OPTION
do
    case $OPTION in
        u)
            USERNAME=$OPTARG
            ;;
        d)
            DBSCHEMA=$OPTARG
            ;;
         h)
	     HOST=$OPTARG
             ;;
         p)
             PORT=$OPTARG
             ;;
         ?)
             usage
             exit
             ;;
     esac
done

# Make sure all required options are supplied
if [[ -z $USERNAME ]] || [[ -z $DBSCHEMA ]]
then
     usage
     exit 1
fi
# Read password from stdin
read -s -p "Your database password: " PASSWORD
# Construct MySQL command line options
MYSQL_OPTS="--user=$USERNAME --password=$PASSWORD"
if [[ ! -z $HOST ]]
then
    MYSQL_OPTS="$MYSQL_OPTS --host=$HOST"
fi
if [[ ! -z $PORT ]]
then
    MYSQL_OPTS="$MYSQL_OPTS --port=$PORT"
fi
# Get the table names
TABLES=$(cat useless_tables_for_nitrate | tr '\n' ',' | sed -e 's/,$//' | awk '{print "SET FOREIGN_KEY_CHECKS = 0;DROP TABLE IF EXISTS " $1 ";SET FOREIGN_KEY_CHECKS = 1;"}')
# Actually drop the tables
mysql $MYSQL_OPTS -BNe "$TABLES" $DBSCHEMA
echo ""
echo "remove useless table done!"


for file in $2/*-in.json; do
	outfile=`echo $file | sed 's/in/out/'`
	output=`./$1 < $file`
	echo ""
	echo $file
	echo $output | diff - $outfile.corrected -wB
done

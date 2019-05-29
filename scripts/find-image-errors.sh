cd /moonsdata/logs
grep "ERROR.*image analysis" *log | gawk '{m=match($0, /images[^ ]*\.bmp/); if(m > 0){ print substr($0, RSTART, RLENGTH)}}' | sort | uniq | grep repeatability >~/image-list-blob-errors

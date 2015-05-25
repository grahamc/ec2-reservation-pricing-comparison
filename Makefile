clean:
	rm -f price.json price.fmt.json out/*

price.json:
	curl https://a0.awsstatic.com/pricing/1/ec2/ri-v2/linux-unix-shared.min.js?callback=callback > price.json

price.fmt.json: price.json
	echo "SEE YOUR BROWSER FOR THE NEXT INSTRUCTION"
	open checkprice.html
	while [ ! -f price.fmt.json ]; do sleep 1; done

out: price.fmt.json
	./compare.rb

upload: out
	AWS_DEFAULT_PROFILE=personal aws s3 sync out/ s3://ec2.gsc.io


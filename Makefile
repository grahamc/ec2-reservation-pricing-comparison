all: clean out upload

clean:
	rm -rf price.json out/

price.json:
	curl -o price.json \
		https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json

out: price.json
	mkdir -p out
	./generate.py

upload: out
	AWS_DEFAULT_PROFILE=personal aws s3 sync out/ s3://ec2.gsc.io

#!/bin/bash

curl http://localhost:5000/predictions -X POST -H "Content-Type: application/json" \
     -d '{
    "input": {
	"prompt": "zelda",
	"width": "512",
	"height": "512",
	"num_outputs": "1"
    }
}'

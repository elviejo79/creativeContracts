#!/bin/bash

# Get back the same json we are sending
curl -H "Content-type: application/json" -X POST -d @test_data.json https://d1f03201.ngrok.io/contrato/new

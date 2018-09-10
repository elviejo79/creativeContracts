#!/usr/bin/env node

const fetch = require("node-fetch");

// import {fetch} from 'wix-fetch';
// export function TrialRequest_beforeInsert(item, context) {
//     return create_pdf(item);
// }

function create_pdf(item){
    const url_pdf_generator = 'https://creativecontracts.ngrok.io/contrato/new';
    
    return fetch(url_pdf_generator, {
        method: 'post',
        headers: {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(item)
    })
        .then(res=>res.json())
        .then(res => {
            item.legalContractUrl= res.legalContractUrl;
            item.legalContractHash = res.legalContractHash;
            console.log(item);
            return item;})
        .catch((err)=>{console.log(err)});
}

// main part of the script
const item = require('./test_data.json');
create_pdf(item);


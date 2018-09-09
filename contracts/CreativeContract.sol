pragma solidity ^0.4.24;

contract CreativeContract {

  // TODO Extract handling due and settlement dates in modifiers

  // Dates (unix timestamp)
  uint256 settlementTimestamp;
  uint256 duedateTimestamp;
  // uint256 contractTimestamp; // handled by the blockchain

  uint256 amount;     // Price of the service
  uint256 oracleFee;  // Amount to be payed to the oracle

  string legalContractUrl;    // URL to the textual contract.
  bytes32 legalContractHash;  // SHA256 of the textual contract.

  // Parties
  address business;  // owner
  address customer;
  address oracle;

  // ============== INTERNALS

  mapping(address => bool) cancelIntent;  // Track the intent of contract cancelation
  mapping(address => bool) settleIntent;  // Track the intent of settle the contract
  mapping(address => bool) rebateIntent;  // Track the intent of contract rebate

  constructor(address _customer,
              address _oracle,
              uint256 _amount,
              uint256 _oracleFee,
              string _lcUrl,
              bytes32 _lcHash,
              uint256 _settlementTs,
              uint256 _dueTs
              ) public {
    // Parties
    business = msg.sender;  // TODO Validate is not same as business or oracle
    customer = _customer;   // TODO Validate is not same as business or oracle
    oracle = _oracle;       // TODO Validate is not the same as business or oracle

    // Amounts
    amount = _amount;
    oracleFee = _oracleFee;  // TODO Validate fee is less than amount

    // Textual contract
    legalContractUrl = _lcUrl;
    legalContractHash = _lcHash;

    // Dates
    // TODO Validate duedateTimestamp < settlementTimestamp
    settlementTimestamp = _settlementTs;
    duedateTimestamp = _dueTs;
  }

  function cancel() public returns (bool) {
    // TODO When a contract can be canceled?

    require(msg.sender == business || msg.sender == customer);
    cancelIntent[msg.sender] = true;

    if (cancelIntent[business] && cancelIntent[customer]) {
      selfdestruct(business);
    }
  }

  function settle() public returns (bool) {
    require(address(this).balance >= oracleFee, "Need to fund the contract first");
    require(msg.sender == customer || msg.sender == business);
    require(now > settlementTimestamp, "Can't settle before contract's settlement date");

    if (msg.sender == business) {
        settleIntent[business] = true;
        return false;
    } else if (msg.sender == oracle) {
        require(settleIntent[business], "Business doesn't want settle");
        oracle.transfer(oracleFee);
        selfdestruct(business);  // TODO Or business.transfer(amount - oracleFee) ?
        return true;
    }
  }

  function rebate() public returns (bool) {
    require(address(this).balance >= oracleFee, "Need to fund the contract first");
    require(msg.sender == customer || msg.sender == oracle);
    require(now > settlementTimestamp, "Can rebate only settled contracts");

    if (msg.sender == customer) {
      rebateIntent[customer] = true;
      return false;
    } else if (msg.sender == oracle) {
      require(rebateIntent[customer], "Customer doesn't want rebate");
      oracle.transfer(oracleFee);
      selfdestruct(customer);  // TODO Or customer.transfer(amount - oracleFee) ?
      return true;
    }
  }

  function fund() public payable {
    // TODO Anyone can fund the contract?

    uint256 balance = address(this).balance;
    uint256 debt = amount - balance; // TODO Use safe math
    require(balance < amount, "Contract is already fully paid");
    require(msg.value <= debt, "Can't over paid the contract");

    if (now > duedateTimestamp) {  // Contract is due
      // call claim()
    } else {
      if (balance == 0) { // Is the first payment?
        require(msg.value >= oracleFee, "Need to cover at least oracle expenses");
      }

      // Blockchain handles the money
    }
  }

  function claim() public returns (bool) {
    require(msg.sender == business);
    require(now > duedateTimestamp, "Can only claim if contract is due");
    selfdestruct(business);
    return true;
  }
}

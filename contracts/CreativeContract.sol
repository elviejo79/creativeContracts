pragma solidity ^0.4.24;

contract CreativeContract {

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

    // call by both the owner and the customer
    // if cancelIntent contains both business and customer's addresses?
    // // destroy contract
  }

  function settle() public returns (bool) {
    // require balance is at least the oracle fee

    // if msg.sender == business
    // // register business settle intent
    // // return

    // else msg.sender == oracle
    // // require settleIntent contains business (owner)
    // // require now > settlementTimestamp (contract settlement date has passed)
    // // require amount == balance (contract is fully paid)
    // // send fee to oracle from the balance
    // // destroy contract
  }

  function rebate() public returns (bool) {
    // require balance is at least the oracle fee

    // if msg.sender == customer
    // // register customer rebate intent
    // // return

    // else msg.sender == oracle
    // // require rebateIntent contains customer
    // // require now > settlementTimestamp (contract settlement date has passed)
    // // send fee to oracle
    // // send balance to customer
    // // destroy contract
  }

  function fund() public payable {
    // TODO Anyone can fund the contract?

    // require balance < amount  (contract hasn't been fully paid)
    // require msg.value <= amount - balance (can't send more than what's left)
    // require now < duedateTimestamp (due date is still in the future)

    // if balance == 0: require msg.value >= oracleFee (at least the oracle fee is covered)
  }

  function claim() public returns (bool) {
    // call by owner
    // require now > duedateTimestamp (pay day is due)
    // destroy contract
  }
}

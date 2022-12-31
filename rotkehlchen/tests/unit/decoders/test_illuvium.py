import pytest

from rotkehlchen.accounting.structures.balance import Balance
from rotkehlchen.accounting.structures.base import HistoryBaseEntry
from rotkehlchen.accounting.structures.types import HistoryEventSubType, HistoryEventType
from rotkehlchen.chain.ethereum.decoding.decoder import EthereumTransactionDecoder
from rotkehlchen.chain.ethereum.modules.illuvium.constants import CPT_ILLUVIUM
from rotkehlchen.chain.ethereum.node_inquirer import EthereumInquirer
from rotkehlchen.chain.ethereum.transactions import EthereumTransactions
from rotkehlchen.chain.evm.decoding.constants import CPT_GAS
from rotkehlchen.chain.evm.structures import EvmTxReceipt, EvmTxReceiptLog
from rotkehlchen.chain.evm.types import string_to_evm_address
from rotkehlchen.constants import ZERO
from rotkehlchen.constants.assets import A_ETH, A_ILV, A_SILV_V1, A_SILV_V2, A_SLP_ILV_ETH
from rotkehlchen.db.dbhandler import DBHandler
from rotkehlchen.db.evmtx import DBEvmTx
from rotkehlchen.fval import FVal
from rotkehlchen.types import (
    ChainID,
    EvmTransaction,
    Location,
    Timestamp,
    TimestampMS,
    deserialize_evm_tx_hash,
)
from rotkehlchen.utils.hexbytes import hexstring_to_bytes


@pytest.mark.parametrize('ethereum_accounts', [['0xDf22269fD88318FB13956b6329BB5959AA06181d']])
def test_v1_ilv_eth_pool_silv_claim(
        database,
        ethereum_inquirer,
        eth_transactions,
):
    receipt = EvmTxReceipt(
        tx_hash=TEST_EVM_HASH,
        chain_id=ChainID.ETHEREUM,
        contract_address=None,
        status=True,
        type=0,
        logs=[
            EvmTxReceiptLog(  # Transfer event
                log_index=420,
                data=hexstring_to_bytes('0x00000000000000000000000000000000000000000000000003105E9EE965119A'),  # noqa: E501
                address=string_to_evm_address('0x398AeA1c9ceb7dE800284bb399A15e0Efe5A9EC2'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),  # noqa: E501
                    hexstring_to_bytes('0x0000000000000000000000000000000000000000000000000000000000000000'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
            EvmTxReceiptLog(  # Claim event
                log_index=421,
                data=hexstring_to_bytes('0x000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000003105E9EE965119A'),  # noqa: E501
                address=string_to_evm_address('0x8B4d8443a0229349A9892D4F7CbE89eF5f843F72'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0x5033fdcf01566fb38fe1493114b856ff2a5d1c7875a6fafdacd1d320a012806a'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
        ],
    )

    events = get_decoded_events(
        database,
        eth_transactions,
        ethereum_inquirer,
        TEST_TRANSACTION,
        receipt,
    )

    assert len(events) == 2
    expected_events = [
        TRANSACTION_FEE_EVENT,
        HistoryBaseEntry(
            event_identifier=TEST_EVM_HASH,
            sequence_index=421,
            timestamp=TimestampMS(1639307389000),
            location=Location.BLOCKCHAIN,
            event_type=HistoryEventType.RECEIVE,
            event_subtype=HistoryEventSubType.REWARD,
            asset=A_SILV_V1,
            balance=Balance(amount=FVal('0.220780418354712986'), usd_value=ZERO),
            location_label=TEST_USER_ADDRESS,
            notes='Claim 0.220780418354712986 sILV',
            counterparty=CPT_ILLUVIUM,
            extra_data={'claimed_amount': '0.220780418354712986', 'asset': 'sILV'},
        )]
    assert events == expected_events


@pytest.mark.parametrize('ethereum_accounts', [['0xDf22269fD88318FB13956b6329BB5959AA06181d']])
def test_v1_ilv_eth_pool_ilv_claim(
        database,
        ethereum_inquirer,
        eth_transactions,
):
    receipt = EvmTxReceipt(
        tx_hash=TEST_EVM_HASH,
        chain_id=ChainID.ETHEREUM,
        contract_address=None,
        status=True,
        type=0,
        logs=[
            EvmTxReceiptLog(  # Claim event
                log_index=421,
                data=hexstring_to_bytes('0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000041ed9a0a90faa14b'),  # noqa: E501
                address=string_to_evm_address('0x8B4d8443a0229349A9892D4F7CbE89eF5f843F72'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0x5033fdcf01566fb38fe1493114b856ff2a5d1c7875a6fafdacd1d320a012806a'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
        ],
    )

    events = get_decoded_events(
        database,
        eth_transactions,
        ethereum_inquirer,
        TEST_TRANSACTION,
        receipt,
    )

    assert len(events) == 3
    expected_events = [
        TRANSACTION_FEE_EVENT,
        HistoryBaseEntry(
            event_identifier=TEST_EVM_HASH,
            sequence_index=422,
            timestamp=TimestampMS(1639307389000),
            location=Location.BLOCKCHAIN,
            event_type=HistoryEventType.RECEIVE,
            event_subtype=HistoryEventSubType.REWARD,
            asset=A_ILV,
            balance=Balance(amount=FVal('4.750622552118436171'), usd_value=ZERO),
            location_label=TEST_USER_ADDRESS,
            notes='Claim 4.750622552118436171 ILV',
            counterparty=CPT_ILLUVIUM,
            extra_data={'claimed_amount': '4.750622552118436171', 'asset': 'ILV'},
        ),
        HistoryBaseEntry(
            event_identifier=TEST_EVM_HASH,
            sequence_index=423,
            timestamp=TimestampMS(1639307389000),
            location=Location.BLOCKCHAIN,
            event_type=HistoryEventType.STAKING,
            event_subtype=HistoryEventSubType.DEPOSIT_ASSET,
            asset=A_ILV,
            balance=Balance(amount=FVal('4.750622552118436171'), usd_value=ZERO),
            location_label=TEST_USER_ADDRESS,
            notes='Stake 4.750622552118436171 ILV in the ILV pool',
            counterparty=CPT_ILLUVIUM,
            extra_data={'staked_amount': '4.750622552118436171', 'asset': 'ILV'},
        ),
    ]
    assert events == expected_events


@pytest.mark.parametrize('ethereum_accounts', [['0xDf22269fD88318FB13956b6329BB5959AA06181d']])
def test_v1_ilv_eth_pool_staking(
        database,
        ethereum_inquirer,
        eth_transactions,
):
    receipt = EvmTxReceipt(
        tx_hash=TEST_EVM_HASH,
        chain_id=ChainID.ETHEREUM,
        contract_address=None,
        status=True,
        type=0,
        logs=[
            EvmTxReceiptLog(  # Transfer event
                log_index=245,
                data=hexstring_to_bytes('0x00000000000000000000000000000000000000000000000009562ac1b79ac10a'),  # noqa: E501
                address=string_to_evm_address('0x6a091a3406E0073C3CD6340122143009aDac0EDa'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                    hexstring_to_bytes('0x0000000000000000000000008B4d8443a0229349A9892D4F7CbE89eF5f843F72'),  # noqa: E501
                ],
            ),
            EvmTxReceiptLog(  # Staked event
                log_index=246,
                data=hexstring_to_bytes('0x00000000000000000000000000000000000000000000000009562ac1b79ac10a'),  # noqa: E501
                address=string_to_evm_address('0x8B4d8443a0229349A9892D4F7CbE89eF5f843F72'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0x5dac0c1b1112564a045ba943c9d50270893e8e826c49be8e7073adc713ab7bd7'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
        ],
    )

    events = get_decoded_events(
        database,
        eth_transactions,
        ethereum_inquirer,
        TEST_TRANSACTION,
        receipt,
    )

    assert len(events) == 2
    expected_events = [
        TRANSACTION_FEE_EVENT,
        HistoryBaseEntry(
            event_identifier=TEST_EVM_HASH,
            sequence_index=246,
            timestamp=TimestampMS(1639307389000),
            location=Location.BLOCKCHAIN,
            event_type=HistoryEventType.STAKING,
            event_subtype=HistoryEventSubType.DEPOSIT_ASSET,
            asset=A_SLP_ILV_ETH,
            balance=Balance(amount=FVal('0.67277220583589505'), usd_value=ZERO),
            location_label=TEST_USER_ADDRESS,
            notes='Stake 0.67277220583589505 SLP in the ILV/ETH pool',
            counterparty=CPT_ILLUVIUM,
            extra_data={'staked_amount': '0.67277220583589505', 'asset': 'SLP'},
        )]
    assert events == expected_events


@pytest.mark.parametrize('ethereum_accounts', [['0xDf22269fD88318FB13956b6329BB5959AA06181d']])
def test_v1_ilv_eth_pool_unstaking(
        database,
        ethereum_inquirer,
        eth_transactions,
):
    receipt = EvmTxReceipt(
        tx_hash=TEST_EVM_HASH,
        chain_id=ChainID.ETHEREUM,
        contract_address=None,
        status=True,
        type=0,
        logs=[
            EvmTxReceiptLog(  # Transfer event
                log_index=245,
                data=hexstring_to_bytes('0x0000000000000000000000000000000000000000000000003cb5a1cd15c74517'),  # noqa: E501
                address=string_to_evm_address('0x6a091a3406E0073C3CD6340122143009aDac0EDa'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),  # noqa: E501
                    hexstring_to_bytes('0x0000000000000000000000008B4d8443a0229349A9892D4F7CbE89eF5f843F72'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
            EvmTxReceiptLog(  # Staked event
                log_index=246,
                data=hexstring_to_bytes('0x0000000000000000000000000000000000000000000000003cb5a1cd15c74517'),  # noqa: E501
                address=string_to_evm_address('0x8B4d8443a0229349A9892D4F7CbE89eF5f843F72'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0xd8654fcc8cf5b36d30b3f5e4688fc78118e6d68de60b9994e09902268b57c3e3'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
        ],
    )

    events = get_decoded_events(
        database,
        eth_transactions,
        ethereum_inquirer,
        TEST_TRANSACTION,
        receipt,
    )

    assert len(events) == 2
    expected_events = [
        TRANSACTION_FEE_EVENT,
        HistoryBaseEntry(
            event_identifier=TEST_EVM_HASH,
            sequence_index=246,
            timestamp=TimestampMS(1639307389000),
            location=Location.BLOCKCHAIN,
            event_type=HistoryEventType.STAKING,
            event_subtype=HistoryEventSubType.REMOVE_ASSET,
            asset=A_SLP_ILV_ETH,
            balance=Balance(amount=FVal('4.374580515266053399'), usd_value=ZERO),
            location_label=TEST_USER_ADDRESS,
            notes='Unstake 4.374580515266053399 SLP from the ILV/ETH pool',
            counterparty=CPT_ILLUVIUM,
            extra_data={'unstaked_amount': '4.374580515266053399', 'asset': 'SLP'},
        )]
    assert events == expected_events


@pytest.mark.parametrize('ethereum_accounts', [['0xDf22269fD88318FB13956b6329BB5959AA06181d']])
def test_v1_ilv_pool_silv_claim(
        database,
        ethereum_inquirer,
        eth_transactions,
):
    receipt = EvmTxReceipt(
        tx_hash=TEST_EVM_HASH,
        chain_id=ChainID.ETHEREUM,
        contract_address=None,
        status=True,
        type=0,
        logs=[
            EvmTxReceiptLog(  # Transfer event
                log_index=420,
                data=hexstring_to_bytes('0x00000000000000000000000000000000000000000000000003105E9EE965119A'),  # noqa: E501
                address=string_to_evm_address('0x398AeA1c9ceb7dE800284bb399A15e0Efe5A9EC2'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),  # noqa: E501
                    hexstring_to_bytes('0x0000000000000000000000000000000000000000000000000000000000000000'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
            EvmTxReceiptLog(  # Claim event
                log_index=421,
                data=hexstring_to_bytes('0x000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000003105E9EE965119A'),  # noqa: E501
                address=string_to_evm_address('0x25121EDDf746c884ddE4619b573A7B10714E2a36'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0x5033fdcf01566fb38fe1493114b856ff2a5d1c7875a6fafdacd1d320a012806a'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
        ],
    )

    events = get_decoded_events(
        database,
        eth_transactions,
        ethereum_inquirer,
        TEST_TRANSACTION,
        receipt,
    )

    assert len(events) == 2
    expected_events = [
        TRANSACTION_FEE_EVENT,
        HistoryBaseEntry(
            event_identifier=TEST_EVM_HASH,
            sequence_index=421,
            timestamp=TimestampMS(1639307389000),
            location=Location.BLOCKCHAIN,
            event_type=HistoryEventType.RECEIVE,
            event_subtype=HistoryEventSubType.REWARD,
            asset=A_SILV_V1,
            balance=Balance(amount=FVal('0.220780418354712986'), usd_value=ZERO),
            location_label=TEST_USER_ADDRESS,
            notes='Claim 0.220780418354712986 sILV',
            counterparty=CPT_ILLUVIUM,
            extra_data={'claimed_amount': '0.220780418354712986', 'asset': 'sILV'},
        )]
    assert events == expected_events


@pytest.mark.parametrize('ethereum_accounts', [['0xDf22269fD88318FB13956b6329BB5959AA06181d']])
def test_v1_ilv_pool_ilv_claim(
        database,
        ethereum_inquirer,
        eth_transactions,
):
    receipt = EvmTxReceipt(
        tx_hash=TEST_EVM_HASH,
        chain_id=ChainID.ETHEREUM,
        contract_address=None,
        status=True,
        type=0,
        logs=[
            EvmTxReceiptLog(  # Claim event
                log_index=421,
                data=hexstring_to_bytes('0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000041ed9a0a90faa14b'),  # noqa: E501
                address=string_to_evm_address('0x25121EDDf746c884ddE4619b573A7B10714E2a36'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0x5033fdcf01566fb38fe1493114b856ff2a5d1c7875a6fafdacd1d320a012806a'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
        ],
    )

    events = get_decoded_events(
        database,
        eth_transactions,
        ethereum_inquirer,
        TEST_TRANSACTION,
        receipt,
    )

    assert len(events) == 3
    expected_events = [
        TRANSACTION_FEE_EVENT,
        HistoryBaseEntry(
            event_identifier=TEST_EVM_HASH,
            sequence_index=422,
            timestamp=TimestampMS(1639307389000),
            location=Location.BLOCKCHAIN,
            event_type=HistoryEventType.RECEIVE,
            event_subtype=HistoryEventSubType.REWARD,
            asset=A_ILV,
            balance=Balance(amount=FVal('4.750622552118436171'), usd_value=ZERO),
            location_label=TEST_USER_ADDRESS,
            notes='Claim 4.750622552118436171 ILV',
            counterparty=CPT_ILLUVIUM,
            extra_data={'claimed_amount': '4.750622552118436171', 'asset': 'ILV'},
        ),
        HistoryBaseEntry(
            event_identifier=TEST_EVM_HASH,
            sequence_index=423,
            timestamp=TimestampMS(1639307389000),
            location=Location.BLOCKCHAIN,
            event_type=HistoryEventType.STAKING,
            event_subtype=HistoryEventSubType.DEPOSIT_ASSET,
            asset=A_ILV,
            balance=Balance(amount=FVal('4.750622552118436171'), usd_value=ZERO),
            location_label=TEST_USER_ADDRESS,
            notes='Stake 4.750622552118436171 ILV in the ILV pool',
            counterparty=CPT_ILLUVIUM,
            extra_data={'staked_amount': '4.750622552118436171', 'asset': 'ILV'},
        ),
    ]
    assert events == expected_events


@pytest.mark.parametrize('ethereum_accounts', [['0xDf22269fD88318FB13956b6329BB5959AA06181d']])
def test_v1_ilv_pool_staking(
        database,
        ethereum_inquirer,
        eth_transactions,
):
    receipt = EvmTxReceipt(
        tx_hash=TEST_EVM_HASH,
        chain_id=ChainID.ETHEREUM,
        contract_address=None,
        status=True,
        type=0,
        logs=[
            EvmTxReceiptLog(  # Transfer event
                log_index=245,
                data=hexstring_to_bytes('0x00000000000000000000000000000000000000000000000009562ac1b79ac10a'),  # noqa: E501
                address=string_to_evm_address('0x767FE9EDC9E0dF98E07454847909b5E959D7ca0E'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                    hexstring_to_bytes('0x00000000000000000000000025121EDDf746c884ddE4619b573A7B10714E2a36'),  # noqa: E501
                ],
            ),
            EvmTxReceiptLog(  # Staked event
                log_index=246,
                data=hexstring_to_bytes('0x00000000000000000000000000000000000000000000000009562ac1b79ac10a'),  # noqa: E501
                address=string_to_evm_address('0x25121EDDf746c884ddE4619b573A7B10714E2a36'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0x5dac0c1b1112564a045ba943c9d50270893e8e826c49be8e7073adc713ab7bd7'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
        ],
    )

    events = get_decoded_events(
        database,
        eth_transactions,
        ethereum_inquirer,
        TEST_TRANSACTION,
        receipt,
    )

    assert len(events) == 2
    expected_events = [
        TRANSACTION_FEE_EVENT,
        HistoryBaseEntry(
            event_identifier=TEST_EVM_HASH,
            sequence_index=246,
            timestamp=TimestampMS(1639307389000),
            location=Location.BLOCKCHAIN,
            event_type=HistoryEventType.STAKING,
            event_subtype=HistoryEventSubType.DEPOSIT_ASSET,
            asset=A_ILV,
            balance=Balance(amount=FVal('0.67277220583589505'), usd_value=ZERO),
            location_label=TEST_USER_ADDRESS,
            notes='Stake 0.67277220583589505 ILV in the ILV pool',
            counterparty=CPT_ILLUVIUM,
            extra_data={'staked_amount': '0.67277220583589505', 'asset': 'ILV'},
        )]
    assert events[1] == expected_events[1]


@pytest.mark.parametrize('ethereum_accounts', [['0xDf22269fD88318FB13956b6329BB5959AA06181d']])
def test_v1_ilv_pool_unstaking(
        database,
        ethereum_inquirer,
        eth_transactions,
):
    receipt = EvmTxReceipt(
        tx_hash=TEST_EVM_HASH,
        chain_id=ChainID.ETHEREUM,
        contract_address=None,
        status=True,
        type=0,
        logs=[
            EvmTxReceiptLog(  # Transfer event
                log_index=245,
                data=hexstring_to_bytes('0x0000000000000000000000000000000000000000000000003cb5a1cd15c74517'),  # noqa: E501
                address=string_to_evm_address('0x767FE9EDC9E0dF98E07454847909b5E959D7ca0E'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),  # noqa: E501
                    hexstring_to_bytes('0x00000000000000000000000025121EDDf746c884ddE4619b573A7B10714E2a36'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
            EvmTxReceiptLog(  # Staked event
                log_index=246,
                data=hexstring_to_bytes('0x0000000000000000000000000000000000000000000000003cb5a1cd15c74517'),  # noqa: E501
                address=string_to_evm_address('0x25121EDDf746c884ddE4619b573A7B10714E2a36'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0xd8654fcc8cf5b36d30b3f5e4688fc78118e6d68de60b9994e09902268b57c3e3'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
        ],
    )

    events = get_decoded_events(
        database,
        eth_transactions,
        ethereum_inquirer,
        TEST_TRANSACTION,
        receipt,
    )

    assert len(events) == 2
    expected_events = [
        TRANSACTION_FEE_EVENT,
        HistoryBaseEntry(
            event_identifier=TEST_EVM_HASH,
            sequence_index=246,
            timestamp=TimestampMS(1639307389000),
            location=Location.BLOCKCHAIN,
            event_type=HistoryEventType.STAKING,
            event_subtype=HistoryEventSubType.REMOVE_ASSET,
            asset=A_ILV,
            balance=Balance(amount=FVal('4.374580515266053399'), usd_value=ZERO),
            location_label=TEST_USER_ADDRESS,
            notes='Unstake 4.374580515266053399 ILV from the ILV pool',
            counterparty=CPT_ILLUVIUM,
            extra_data={'unstaked_amount': '4.374580515266053399', 'asset': 'ILV'},
        )]
    assert events == expected_events


@pytest.mark.parametrize('ethereum_accounts', [['0xDf22269fD88318FB13956b6329BB5959AA06181d']])
def test_v2_silv2_claim(
        database,
        ethereum_inquirer,
        eth_transactions,
):
    receipt = EvmTxReceipt(
        tx_hash=TEST_EVM_HASH,
        chain_id=ChainID.ETHEREUM,
        contract_address=None,
        status=True,
        type=0,
        logs=[
            EvmTxReceiptLog(  # Transfer event
                log_index=245,
                data=hexstring_to_bytes('0x0000000000000000000000000000000000000000000000000163ab22590e3cef'),  # noqa: E501
                address=string_to_evm_address('0x7E77dCb127F99ECe88230a64Db8d595F31F1b068'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),  # noqa: E501
                    hexstring_to_bytes('0x0000000000000000000000000000000000000000000000000000000000000000'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000Df22269fD88318FB13956b6329BB5959AA06181d'),  # noqa: E501
                ],
            ),
            EvmTxReceiptLog(  # LogClaim event
                log_index=421,
                data=hexstring_to_bytes('0x0000000000000000000000000000000000000000000000000163ab22590e3cef'),  # noqa: E501
                address=string_to_evm_address('0xA904f27b1DE7e82Ba587677eE1f5af0AD0A8c79A'),
                removed=False,
                topics=[
                    hexstring_to_bytes('0x51223fdc0a25891366fb358b4af9fe3c381b1566e287c61a29d01c8a173fe4f4'),  # noqa: E501
                    hexstring_to_bytes('0x000000000000000000000000000000000000000000000000000000000000083a'),  # noqa: E501
                    hexstring_to_bytes('0x00000000000000000000000028e99f920d0c52727b45e7aa535786cda5c9ac67'),  # noqa: E501
                ],
            ),
        ],
    )

    events = get_decoded_events(
        database,
        eth_transactions,
        ethereum_inquirer,
        TEST_TRANSACTION,
        receipt,
    )

    assert len(events) == 2
    expected_events = [
        TRANSACTION_FEE_EVENT,
        HistoryBaseEntry(
            event_identifier=TEST_EVM_HASH,
            sequence_index=246,
            timestamp=TimestampMS(1639307389000),
            location=Location.BLOCKCHAIN,
            event_type=HistoryEventType.MIGRATE,
            event_subtype=HistoryEventSubType.RECEIVE,
            asset=A_SILV_V2,
            balance=Balance(amount=FVal('0.100111780743625967'), usd_value=ZERO),
            location_label=TEST_USER_ADDRESS,
            notes='Migrated 0.100111780743625967 sILV2 from sILV1',
            counterparty=CPT_ILLUVIUM,
        )]
    assert events[1] == expected_events[1]


def get_decoded_events(
        database: DBHandler,
        eth_transactions: EthereumTransactions,
        ethereum_inquirer: EthereumInquirer,
        transaction: EvmTransaction,
        receipt: EvmTxReceipt,
):
    dbevmtx = DBEvmTx(database)
    with database.user_write() as cursor:
        dbevmtx.add_evm_transactions(cursor, [transaction], relevant_address=None)
        decoder = EthereumTransactionDecoder(
            database=database,
            ethereum_inquirer=ethereum_inquirer,
            transactions=eth_transactions,
        )
        events = decoder.decode_transaction(cursor, transaction=transaction, tx_receipt=receipt)
    return events


TEST_TX_HEX = '0xaf722bd1b29ed59dc2648c051d46ff129535980b25fc86d9814f57c38db2a18a'
TEST_USER_ADDRESS = string_to_evm_address('0xDf22269fD88318FB13956b6329BB5959AA06181d')
TEST_EVM_HASH = deserialize_evm_tx_hash(TEST_TX_HEX)

TRANSACTION_FEE_EVENT = HistoryBaseEntry(
    event_identifier=TEST_EVM_HASH,
    sequence_index=0,
    timestamp=TimestampMS(1639307389000),
    location=Location.BLOCKCHAIN,
    event_type=HistoryEventType.SPEND,
    event_subtype=HistoryEventSubType.FEE,
    asset=A_ETH,
    balance=Balance(
        amount=FVal('0.00961145144911261'),
        usd_value=ZERO,
    ),
    location_label=TEST_USER_ADDRESS,
    notes='Burned 0.00961145144911261 ETH for gas',
    counterparty=CPT_GAS,
)

TEST_TRANSACTION = EvmTransaction(
    tx_hash=TEST_EVM_HASH,
    chain_id=ChainID.ETHEREUM,
    timestamp=Timestamp(1639307389),
    block_number=13789926,
    from_address=TEST_USER_ADDRESS,
    to_address=string_to_evm_address('0x8B4d8443a0229349A9892D4F7CbE89eF5f843F72'),
    value=0,
    gas=320665,
    gas_price=40204343794,
    gas_used=239065,
    input_data=hexstring_to_bytes('0x52044ec900000000000000000000000000000000000000000000000009562ac1b79ac10a00000000000000000000000000000000000000000000000000000000622496620000000000000000000000000000000000000000000000000000000000000000'),  # noqa: E501
    nonce=34,
)

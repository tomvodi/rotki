import logging
from typing import TYPE_CHECKING, Any, Optional

from rotkehlchen.accounting.structures.balance import Balance
from rotkehlchen.accounting.structures.base import HistoryBaseEntry
from rotkehlchen.accounting.structures.types import HistoryEventSubType, HistoryEventType
from rotkehlchen.chain.ethereum.modules.illuvium.constants import CPT_ILLUVIUM
from rotkehlchen.chain.ethereum.utils import asset_normalized_value
from rotkehlchen.chain.evm.decoding.interfaces import DecoderInterface
from rotkehlchen.chain.evm.decoding.structures import ActionItem
from rotkehlchen.chain.evm.structures import EvmTxReceiptLog
from rotkehlchen.chain.evm.types import string_to_evm_address
from rotkehlchen.constants.assets import A_ILV, A_SILV_V1, A_SLP_ILV_ETH
from rotkehlchen.logging import RotkehlchenLogsAdapter
from rotkehlchen.types import ChecksumEvmAddress, EvmTransaction, Location
from rotkehlchen.utils.misc import hex_or_bytes_to_address, hex_or_bytes_to_int, ts_sec_to_ms

if TYPE_CHECKING:
    from rotkehlchen.chain.ethereum.node_inquirer import EthereumInquirer
    from rotkehlchen.chain.evm.decoding.base import BaseDecoderTools
    from rotkehlchen.user_messages import MessagesAggregator

ILV_ETH_CORE_POOL_V1 = string_to_evm_address('0x8B4d8443a0229349A9892D4F7CbE89eF5f843F72')
ILV_CORE_POOL_V1 = string_to_evm_address('0x25121EDDf746c884ddE4619b573A7B10714E2a36')
ILV_CORE_POOL_V1_STAKING = b']\xac\x0c\x1b\x11\x12VJ\x04[\xa9C\xc9\xd5\x02p\x89>\x8e\x82lI\xbe\x8eps\xad\xc7\x13\xab{\xd7'  # noqa: E501
ILV_CORE_POOL_V1_UNSTAKING = b'\xd8eO\xcc\x8c\xf5\xb3m0\xb3\xf5\xe4h\x8f\xc7\x81\x18\xe6\xd6\x8d\xe6\x0b\x99\x94\xe0\x99\x02&\x8bW\xc3\xe3'  # noqa: E501
ILV_CORE_POOL_V1_CLAIM = b'P3\xfd\xcf\x01Vo\xb3\x8f\xe1I1\x14\xb8V\xff*]\x1cxu\xa6\xfa\xfd\xac\xd1\xd3 \xa0\x12\x80j'  # noqa: E501

logger = logging.getLogger(__name__)
log = RotkehlchenLogsAdapter(logger)


class IlluviumDecoder(DecoderInterface):

    def __init__(
            self,
            ethereum_inquirer: 'EthereumInquirer',
            base_tools: 'BaseDecoderTools',
            msg_aggregator: 'MessagesAggregator',
    ) -> None:
        super().__init__(
            evm_inquirer=ethereum_inquirer,
            base_tools=base_tools,
            msg_aggregator=msg_aggregator,
        )
        self.base = base_tools

    def _poolname_for_counterparty(self, counterparty: Optional[str]) -> str:
        if counterparty == ILV_ETH_CORE_POOL_V1:
            return 'ILV/ETH'
        if counterparty == ILV_CORE_POOL_V1:
            return 'ILV'
        return 'Unknown'

    def _decode_illuvium_v1_events(
            self,
            tx_log: EvmTxReceiptLog,
            transaction: EvmTransaction,
            decoded_events: list[HistoryBaseEntry],
            all_logs: list[EvmTxReceiptLog],  # pylint: disable=unused-argument
            action_items: Optional[list[ActionItem]],  # pylint: disable=unused-argument
    ) -> tuple[Optional[HistoryBaseEntry], list[ActionItem]]:
        if tx_log.topics[0] not in (
                ILV_CORE_POOL_V1_STAKING,
                ILV_CORE_POOL_V1_UNSTAKING,
                ILV_CORE_POOL_V1_CLAIM,
        ):
            return None, []

        for event in decoded_events:
            if (
                    tx_log.topics[0] == ILV_CORE_POOL_V1_STAKING and
                    event.asset == A_SLP_ILV_ETH or
                    event.asset == A_ILV
            ):
                pool_name = self._poolname_for_counterparty(event.counterparty)
                user = hex_or_bytes_to_address(tx_log.topics[1])
                extra_data = {
                    'staked_amount': str(event.balance.amount),
                    'asset': event.asset.symbol_or_name(),
                }
                if event.location_label == user and event.event_type == HistoryEventType.SPEND:
                    event.event_type = HistoryEventType.STAKING
                    event.event_subtype = HistoryEventSubType.DEPOSIT_ASSET
                    event.counterparty = CPT_ILLUVIUM
                    event.notes = f'Stake {event.balance.amount} {event.asset.symbol_or_name()} in the {pool_name} pool'  # noqa: E501
                    event.extra_data = extra_data

            if (
                    tx_log.topics[0] == ILV_CORE_POOL_V1_UNSTAKING and
                    event.asset == A_SLP_ILV_ETH or
                    event.asset == A_ILV
            ):
                pool_name = self._poolname_for_counterparty(event.counterparty)
                user = hex_or_bytes_to_address(tx_log.topics[1])
                extra_data = {
                    'unstaked_amount': str(event.balance.amount),
                    'asset': event.asset.symbol_or_name(),
                }
                if event.location_label == user and event.event_type == HistoryEventType.RECEIVE:
                    event.event_type = HistoryEventType.STAKING
                    event.event_subtype = HistoryEventSubType.REMOVE_ASSET
                    event.counterparty = CPT_ILLUVIUM
                    event.notes = f'Unstake {event.balance.amount} {event.asset.symbol_or_name()} from the {pool_name} pool'  # noqa: E501
                    event.extra_data = extra_data

            if (
                    tx_log.topics[0] == ILV_CORE_POOL_V1_CLAIM and
                    event.asset == A_SILV_V1
            ):
                extra_data = {
                    'claimed_amount': str(event.balance.amount),
                    'asset': A_SILV_V1.symbol_or_name(),
                }
                event.event_type = HistoryEventType.RECEIVE
                event.event_subtype = HistoryEventSubType.REWARD
                event.counterparty = CPT_ILLUVIUM
                event.notes = f'Claim {event.balance.amount} {A_SILV_V1.symbol_or_name()}'
                event.extra_data = extra_data

        if (
                tx_log.topics[0] == ILV_CORE_POOL_V1_CLAIM
        ):
            user_address = hex_or_bytes_to_address(tx_log.topics[1])
            raw_amount = hex_or_bytes_to_int(tx_log.data[32:64])
            amount = asset_normalized_value(
                amount=raw_amount,
                asset=A_ILV.resolve_to_evm_token(),
            )
            use_silv = hex_or_bytes_to_int(tx_log.data[0:32])
            if use_silv == 1:  # handle only ILV claims here
                return None, []

            claim_sequence_idx = self.base.get_sequence_index(tx_log)

            decoded_events.append(HistoryBaseEntry(
                event_identifier=transaction.tx_hash,
                timestamp=ts_sec_to_ms(transaction.timestamp),
                location=Location.BLOCKCHAIN,
                location_label=user_address,
                asset=A_ILV,
                balance=Balance(amount=amount),
                counterparty=CPT_ILLUVIUM,
                sequence_index=claim_sequence_idx,
                event_type=HistoryEventType.RECEIVE,
                event_subtype=HistoryEventSubType.REWARD,
                notes=f'Claim {amount} {A_ILV.symbol_or_name()}',
                extra_data={
                    'claimed_amount': str(amount),
                    'asset': A_ILV.symbol_or_name(),
                },
            ))

            decoded_events.append(HistoryBaseEntry(
                event_identifier=transaction.tx_hash,
                timestamp=ts_sec_to_ms(transaction.timestamp),
                location=Location.BLOCKCHAIN,
                location_label=user_address,
                asset=A_ILV,
                balance=Balance(amount=amount),
                counterparty=CPT_ILLUVIUM,
                sequence_index=claim_sequence_idx + 1,
                event_type=HistoryEventType.STAKING,
                event_subtype=HistoryEventSubType.DEPOSIT_ASSET,
                notes=f'Stake {amount} {A_ILV.symbol_or_name()} in the '
                      f'{self._poolname_for_counterparty(ILV_CORE_POOL_V1)} pool',
                extra_data={
                    'staked_amount': str(amount),
                    'asset': A_ILV.symbol_or_name(),
                },
            ))

        return None, []

    def addresses_to_decoders(self) -> dict[ChecksumEvmAddress, tuple[Any, ...]]:
        return {
            ILV_ETH_CORE_POOL_V1: (self._decode_illuvium_v1_events,),
            ILV_CORE_POOL_V1: (self._decode_illuvium_v1_events,),
        }

    def counterparties(self) -> list[str]:
        return [CPT_ILLUVIUM]

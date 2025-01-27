import pyshark
from pyflowmeter.meter import Meter
import time
import os

def capture_and_analyze(interface='eth0', output_file='network_traffic.pcap', capture_filter='ip or tcp or udp', duration=60):
    """
    Captures network traffic and analyzes flows using PyFlowMeter.
    
    Args:
        interface (str): Network interface to listen on (e.g., 'eth0').
        output_file (str): Path to save the captured packets in .pcap format.
        capture_filter (str): BPF capture filter for packet filtering.
        duration (int): Duration (in seconds) for capturing traffic.
    
    Returns:
        None
    """
    print(f"Starting capture on interface {interface} for {duration} seconds...")

    # Set up the flow meter
    meter = Meter()

    try:
        # Start capturing packets with PyShark
        capture = pyshark.LiveCapture(
            interface=interface,
            output_file=output_file,
            bpf_filter=capture_filter
        )
        
        # Sniff packets for the specified duration
        end_time = time.time() + duration
        for packet in capture.sniff_continuously():
            # Check if capture duration has been reached
            if time.time() > end_time:
                break

            try:
                # Feed each packet into the flow meter
                meter.add_packet(packet)
            except Exception as e:
                print(f"Error processing packet: {e}")

        # Export flow statistics to a CSV file
        flows_csv = 'flow_statistics.csv'
        meter.export_to_csv(flows_csv)
        
        print(f"Capture complete. {len(capture)} packets saved to {output_file}.")
        print(f"Flow statistics saved to {flows_csv}.")

    except Exception as e:
        print(f"Error during capture or analysis: {e}")

# Usage example
if __name__ == "__main__":
    # Replace 'eth0' with the name of the network interface on your system
    capture_and_analyze(
        interface='eth0',
        output_file='traffic_layer3_4.pcap',
        capture_filter='ip or tcp or udp',
        duration=60
    )

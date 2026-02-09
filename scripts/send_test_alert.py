"""Send a test alert to Alertmanager and exit.

Usage:
  python scripts/send_test_alert.py --alert <name> --labels key=value --labels key2=value2

Defaults: alertname=SmokeTest, severity=warning
"""
import json
import sys
import argparse
import requests

ALERTMANAGER = 'http://localhost:9093/api/v1/alerts'

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--alert', default='SmokeTest')
    p.add_argument('--labels', action='append', default=[])
    args = p.parse_args()

    labels = {'alertname': args.alert, 'severity': 'warning'}
    for lbl in args.labels:
        k, v = lbl.split('=', 1)
        labels[k] = v

    payload = [{
        'labels': labels,
        'annotations': {'summary': 'Smoke test alert'},
    }]

    r = requests.post(ALERTMANAGER, json=payload, timeout=5)
    print('status', r.status_code, r.text)
    r.raise_for_status()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Update feature_list.json to reflect current test status."""

import json
from datetime import datetime, timezone

def update_feature_list():
    with open('feature_list.json', 'r') as f:
        features = json.load(f)

    # Features 18-26 are agent-related features that need proper deepagents integration
    # The current keyword-based implementation works but these features aren't fully tested
    # Mark them as not dev_done to reflect they need proper implementation
    for i in range(18, 27):
        if i < len(features):
            features[i]['is_dev_done'] = False
            features[i]['passes'] = False
            features[i]['is_qa_passed'] = False
            if 'dev_completed_at' in features[i]:
                del features[i]['dev_completed_at']

    # Features 54-60 are admin API and session persistence - not yet implemented
    for i in range(54, 61):
        if i < len(features):
            features[i]['is_dev_done'] = False
            features[i]['passes'] = False
            features[i]['is_qa_passed'] = False

    # Write updated feature list
    with open('feature_list.json', 'w') as f:
        json.dump(features, f, indent=2)

    print("Updated feature_list.json")
    print("\nFeatures 18-26: Marked as NOT dev_done (need deepagents integration)")
    print("Features 54-60: Marked as NOT dev_done (not yet implemented)")

    # Show current stats
    total = len(features)
    qa_pass = sum(1 for f in features if f.get('is_qa_passed', False))
    dev_done = sum(1 for f in features if f.get('is_dev_done', False))

    print(f"\nCurrent Progress:")
    print(f"  Total features: {total}")
    print(f"  QA Passed: {qa_pass} ({qa_pass/total*100:.1f}%)")
    print(f"  Dev Done: {dev_done} ({dev_done/total*100:.1f}%)")

if __name__ == '__main__':
    update_feature_list()

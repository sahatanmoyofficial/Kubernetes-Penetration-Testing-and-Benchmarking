
import json
from pathlib import Path

def load_kube_bench_results(json_path):
    with open(json_path, 'r') as file:
        return json.load(file)

def generate_report(data, output_path="kube_bench_report.md"):
    lines = []
    total_pass, total_fail, total_warn, total_info = 0, 0, 0, 0

    for control in data.get("Controls", []):
        lines.append(f"# Control: {control['text']} ({control['id']})")
        lines.append(f"**Node Type:** {control['node_type']}")
        lines.append("")

        for test in control.get("tests", []):
            section_header = f"## Section {test['section']}: {test['desc']}"
            lines.append(section_header)
            lines.append(f"- **Pass:** {test['pass']}")
            lines.append(f"- **Fail:** {test['fail']}")
            lines.append(f"- **Warn:** {test['warn']}")
            lines.append(f"- **Info:** {test['info']}")
            lines.append("")

            total_pass += test['pass']
            total_fail += test['fail']
            total_warn += test['warn']
            total_info += test['info']

            for result in test.get("results", []):
                lines.append(f"### {result['test_number']} - {result['test_desc']}")
                lines.append(f"- **Status:** {result['status']}")
                if result.get('reason'):
                    lines.append(f"- **Reason:** {result['reason'][:500]}{'...' if len(result['reason']) > 500 else ''}")
                if result.get('remediation'):
                    lines.append(f"- **Remediation:** {result['remediation'].replace(chr(10), ' ')}")
                lines.append("")

        lines.append("\n---\n")

    # Summary
    lines.append("# Summary")
    lines.append(f"- **Total Passed:** {total_pass}")
    lines.append(f"- **Total Failed:** {total_fail}")
    lines.append(f"- **Total Warnings:** {total_warn}")
    lines.append(f"- **Total Info:** {total_info}")
    lines.append("")

    with open(output_path, 'w') as file:
        file.write('\n'.join(lines))

    print(f" Report saved to {output_path}")

if __name__ == "__main__":
    json_input = "kube-bench-results.json"  # Adjust path if needed
    output_file = "kube_bench_report.md"
    data = load_kube_bench_results(json_input)
    generate_report(data, output_file)
# docs/diagrams/arch.py
from diagrams import Diagram, Cluster, Edge

# ---- Safe imports (AWS icons if available, else generic fallbacks) ----
def _fallback():
    from diagrams.generic.compute import Rack
    from diagrams.generic.network import Firewall
    from diagrams.generic.storage import Storage
    from diagrams.generic.network import Subnet
    return Rack, Firewall, Storage, Subnet

Rack, Firewall, Storage, Subnet = _fallback()

# Local / tooling
try:
    from diagrams.onprem.client import User
except Exception:
    from diagrams.generic.user import User

try:
    from diagrams.onprem.iac import Terraform
except Exception:
    Terraform = Rack

# AWS (some modules may not exist depending on diagrams version)
try:
    from diagrams.aws.network import VPC, InternetGateway, NATGateway
except Exception:
    VPC, InternetGateway, NATGateway = Rack, Rack, Rack

# Subnets vary a lot across versions, so keep them generic
PublicSubnet = Subnet
PrivateSubnet = Subnet

try:
    from diagrams.aws.compute import EC2
except Exception:
    EC2 = Rack

try:
    from diagrams.aws.security import IAMRole
except Exception:
    IAMRole = Rack

# CloudWatch icon name can vary
try:
    from diagrams.aws.management import Cloudwatch
except Exception:
    try:
        from diagrams.aws.management import CloudwatchLogs as Cloudwatch
    except Exception:
        Cloudwatch = Storage

# Kubernetes-ish elements (use generic to avoid import issues)
DaemonSet = Rack
ServiceAccount = Rack
Pods = Rack
OIDCProvider = Rack

# ---- Diagram styling (regular white background) ----
graph_attr = {
    "pad": "0.6",
    "splines": "spline",
    "nodesep": "0.7",
    "ranksep": "0.9",
    "fontsize": "12",
    "dpi": "220",
    "bgcolor": "white",
}

node_attr = {
    "fontsize": "11",
}

edge_attr = {
    "fontsize": "10",
}

OUT = "docs/diagrams/gg-logging-cloudwatch-arch"

with Diagram(
    "GG Logging (CloudWatch): Fluent Bit → CloudWatch Logs (IRSA)",
    show=False,
    filename=OUT,
    outformat="png",
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    # Left side (you apply Terraform + kubectl)
    you = User("You\n(local)")
    tf = Terraform("Terraform\n(IaC)")

    you >> Edge(label="terraform init / plan / apply") >> tf

    with Cluster("AWS"):
        with Cluster("Networking"):
            vpc = VPC("VPC")
            pub = PublicSubnet("Public subnet(s)")
            priv = PrivateSubnet("Private subnet(s)")
            igw = InternetGateway("Internet Gateway")
            nat = NATGateway("NAT Gateway\n(optional)")

            vpc >> Edge(label="contains") >> pub
            vpc >> Edge(label="contains") >> priv
            pub >> Edge(style="dashed", label="egress") >> igw
            priv >> Edge(style="dashed", label="egress via") >> nat
            nat >> Edge(style="dashed") >> igw

        with Cluster("EKS"):
            # Use EC2 icon as a clean stand-in if EKS icon isn't available
            eks = Rack("EKS Cluster")
            nodes = Rack("Worker nodes")
            pods = Pods("Workload pods")

            eks >> Edge(label="runs") >> nodes >> Edge(label="run") >> pods

            with Cluster("Logging (kube-system / logging)"):
                oidc = OIDCProvider("OIDC provider")
                irsa = IAMRole("IRSA role\n(assume via OIDC)")
                sa = ServiceAccount("ServiceAccount\n(fluent-bit)\nannotated with role arn")
                ds = DaemonSet("Fluent Bit\nDaemonSet")
                cw = Cloudwatch("CloudWatch Logs\n(Log Group + Streams)")

                oidc >> Edge(label="trust") >> irsa
                irsa >> Edge(label="attached to") >> sa
                sa >> Edge(label="used by") >> ds
                ds >> Edge(label="runs on nodes") >> nodes

                # What actually happens
                pods >> Edge(label="container logs") >> ds
                eks >> Edge(label="control-plane logs") >> cw
                ds >> Edge(label="ships logs") >> cw

    tf >> Edge(label="creates / configures") >> vpc
    tf >> Edge(label="creates / configures") >> eks

"""Add rule_flags, explanation, base_ml_probability to predictions + known_policies/known_vehicles tables

Revision ID: a9f3c2e1b7d4
Revises: b850a1aefd66
Create Date: 2026-06-22 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9f3c2e1b7d4'
down_revision: Union[str, Sequence[str], None] = 'b850a1aefd66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- Seed data from policy.txt and vehicle.txt ---
# These are the 20 valid entries the user can edit in the .txt files.
_POLICY_DATA = [
    ("POL-HDFC-2024-001234", "HDFC Ergo", "Comprehensive", "Rahul Sharma"),
    ("POL-ICICI-2024-005678", "ICICI Lombard", "Comprehensive", "Priya Patel"),
    ("POL-TATA-2024-009012", "TATA AIG", "Third Party", "Amit Kumar"),
    ("POL-BAJAJ-2024-003456", "Bajaj Allianz", "Own Damage", "Neha Singh"),
    ("POL-STAR-2024-007890", "Star Health", "Comprehensive", "Vikram Joshi"),
    ("POL-HDFC-2023-011234", "HDFC Ergo", "Zero Depreciation", "Sneha Reddy"),
    ("POL-ICICI-2023-015678", "ICICI Lombard", "Comprehensive", "Arjun Mehta"),
    ("POL-TATA-2023-019012", "TATA AIG", "Third Party", "Kavita Nair"),
    ("POL-BAJAJ-2023-013456", "Bajaj Allianz", "Comprehensive", "Rajesh Gupta"),
    ("POL-STAR-2023-017890", "Star Health", "Own Damage", "Anita Desai"),
    ("POL-HDFC-2024-021234", "HDFC Ergo", "Comprehensive", "Suresh Verma"),
    ("POL-ICICI-2024-025678", "ICICI Lombard", "Third Party", "Deepika Rao"),
    ("POL-TATA-2024-029012", "TATA AIG", "Zero Depreciation", "Manish Agarwal"),
    ("POL-BAJAJ-2024-023456", "Bajaj Allianz", "Comprehensive", "Pooja Malhotra"),
    ("POL-STAR-2024-027890", "Star Health", "Own Damage", "Nikhil Bansal"),
    ("POL-HDFC-2022-031234", "HDFC Ergo", "Comprehensive", "Rohit Saxena"),
    ("POL-ICICI-2022-035678", "ICICI Lombard", "Third Party", "Swati Pillai"),
    ("POL-TATA-2022-039012", "TATA AIG", "Own Damage", "Harsh Kapoor"),
    ("POL-BAJAJ-2022-033456", "Bajaj Allianz", "Comprehensive", "Meera Iyer"),
    ("POL-STAR-2022-037890", "Star Health", "Zero Depreciation", "Kiran Choudhary"),
]

_VEHICLE_DATA = [
    ("MH-12-AB-1234", "Hyundai", "Creta", "White", "Rahul Sharma"),
    ("DL-01-CX-7890", "Maruti", "Swift", "Silver", "Priya Patel"),
    ("KA-05-MN-4567", "Honda", "City", "Black", "Amit Kumar"),
    ("TN-22-PR-2345", "Tata", "Nexon", "Red", "Neha Singh"),
    ("WB-04-LK-8901", "Mahindra", "XUV700", "Blue", "Vikram Joshi"),
    ("GJ-01-RT-6789", "Hyundai", "Verna", "Grey", "Sneha Reddy"),
    ("RJ-14-SA-3456", "Maruti", "Baleno", "White", "Arjun Mehta"),
    ("UP-16-DT-9012", "Toyota", "Fortuner", "Black", "Kavita Nair"),
    ("TS-09-FG-5678", "Kia", "Seltos", "Blue", "Rajesh Gupta"),
    ("AP-07-HJ-1234", "MG", "Hector", "Silver", "Anita Desai"),
    ("KL-07-BV-6789", "Honda", "Amaze", "Red", "Suresh Verma"),
    ("PB-08-NE-2345", "Hyundai", "i20", "White", "Deepika Rao"),
    ("HR-26-QW-8901", "Maruti", "Brezza", "Black", "Manish Agarwal"),
    ("MP-04-UY-4567", "Tata", "Harrier", "Grey", "Pooja Malhotra"),
    ("MH-14-ZE-3456", "Toyota", "Innova", "White", "Nikhil Bansal"),
    ("DL-08-AC-9012", "Honda", "Civic", "Blue", "Rohit Saxena"),
    ("KA-03-FD-5678", "Hyundai", "Tucson", "Red", "Swati Pillai"),
    ("TN-11-GH-1234", "Mahindra", "Thar", "Black", "Harsh Kapoor"),
    ("GJ-18-JK-6789", "Kia", "Carens", "Silver", "Meera Iyer"),
    ("RJ-02-LM-2345", "Maruti", "Ertiga", "White", "Kiran Choudhary"),
]


def upgrade() -> None:
    # --- Create known_policies table ---
    op.create_table(
        'known_policies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('policy_number', sa.String(100), nullable=False),
        sa.Column('insurer', sa.String(100), nullable=True),
        sa.Column('policy_type', sa.String(50), nullable=True),
        sa.Column('holder_name', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('policy_number'),
    )
    op.create_index('ix_known_policies_policy_number', 'known_policies', ['policy_number'])

    # Seed known policies
    conn = op.get_bind()
    now = sa.text("NOW()")
    for row in _POLICY_DATA:
        conn.execute(
            sa.text(
                "INSERT INTO known_policies (policy_number, insurer, policy_type, holder_name, created_at) "
                "VALUES (:pn, :ins, :pt, :hn, NOW())"
            ),
            {"pn": row[0], "ins": row[1], "pt": row[2], "hn": row[3]},
        )

    # --- Create known_vehicles table ---
    op.create_table(
        'known_vehicles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('license_plate', sa.String(50), nullable=False),
        sa.Column('make', sa.String(100), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('color', sa.String(50), nullable=True),
        sa.Column('owner_name', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('license_plate'),
    )
    op.create_index('ix_known_vehicles_license_plate', 'known_vehicles', ['license_plate'])

    # Seed known vehicles
    for row in _VEHICLE_DATA:
        conn.execute(
            sa.text(
                "INSERT INTO known_vehicles (license_plate, make, model, color, owner_name, created_at) "
                "VALUES (:lp, :mk, :md, :cl, :ow, NOW())"
            ),
            {"lp": row[0], "mk": row[1], "md": row[2], "cl": row[3], "ow": row[4]},
        )

    # --- Add columns to predictions ---
    op.add_column('predictions', sa.Column('rule_flags', sa.JSON(), nullable=True))
    op.add_column('predictions', sa.Column('explanation', sa.Text(), nullable=True))
    op.add_column('predictions', sa.Column('base_ml_probability', sa.Float(), nullable=True))

    # --- Add columns to documents ---
    op.add_column('documents', sa.Column('verification_status', sa.String(50), nullable=True))
    op.add_column('documents', sa.Column('verification_reasoning', sa.Text(), nullable=True))
    op.add_column('documents', sa.Column('extracted_text', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('documents', 'extracted_text')
    op.drop_column('documents', 'verification_reasoning')
    op.drop_column('documents', 'verification_status')
    op.drop_column('predictions', 'base_ml_probability')
    op.drop_column('predictions', 'explanation')
    op.drop_column('predictions', 'rule_flags')
    op.drop_index('ix_known_vehicles_license_plate', table_name='known_vehicles')
    op.drop_table('known_vehicles')
    op.drop_index('ix_known_policies_policy_number', table_name='known_policies')
    op.drop_table('known_policies')

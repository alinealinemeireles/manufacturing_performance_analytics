-- Auto-generated from datasets/processed/*.csv and datasets/dim/*.csv
-- Dimension / master-data and control-plan tables.

CREATE TABLE IF NOT EXISTS `dim_masterbatch` (
  `ProductId` VARCHAR(40),
  `ProductType` VARCHAR(16),
  `MoldId` VARCHAR(18),
  `BaseMaterial` VARCHAR(16),
  `ColorId` VARCHAR(16),
  `ColorName` VARCHAR(38),
  `PantoneCodeApprox` VARCHAR(40),
  `MasterbatchType` VARCHAR(64),
  `StandardDosagePctMass` DOUBLE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_machine_setup` (
  `MoldId` VARCHAR(18),
  `MachineId` VARCHAR(16),
  `Product` VARCHAR(54),
  `Cavities` BIGINT,
  `RatedCapacityPerDay` VARCHAR(38),
  `RatedCapacityPerHour` VARCHAR(28),
  `CyclesPerHour` BIGINT,
  `IdealCycleTimeSec` BIGINT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_cap_control_plan_cq` (
  `Process` VARCHAR(34),
  `Operation` VARCHAR(20),
  `Characteristic` VARCHAR(20),
  `Class` VARCHAR(16),
  `InspectionType` VARCHAR(18),
  `Specification` VARCHAR(48),
  `Method` VARCHAR(22),
  `Equipment` VARCHAR(30),
  `Standard` VARCHAR(20),
  `ISOLevel` VARCHAR(16),
  `AQL` VARCHAR(16),
  `Frequency` VARCHAR(24),
  `LotSize` VARCHAR(28),
  `ISOCode` VARCHAR(16),
  `SampleSize` VARCHAR(18),
  `AcceptanceNumber` VARCHAR(20),
  `RejectionNumber` VARCHAR(20),
  `Owner` VARCHAR(20),
  `ReactionPlan` VARCHAR(44)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_bottle_control_plan_cq` (
  `Process` VARCHAR(24),
  `Operation` VARCHAR(20),
  `Characteristic` VARCHAR(30),
  `Class` VARCHAR(16),
  `InspectionType` VARCHAR(18),
  `Specification` VARCHAR(48),
  `Method` VARCHAR(20),
  `Equipment` VARCHAR(36),
  `Standard` VARCHAR(20),
  `ISOLevel` VARCHAR(16),
  `AQL` VARCHAR(16),
  `Frequency` VARCHAR(24),
  `LotSize` VARCHAR(44),
  `ISOCode` VARCHAR(16),
  `SampleSize` VARCHAR(16),
  `AcceptanceNumber` VARCHAR(20),
  `RejectionNumber` VARCHAR(20),
  `Owner` VARCHAR(20),
  `ReactionPlan` VARCHAR(38)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_ink_control_plan_cq` (
  `Process` VARCHAR(30),
  `Operation` VARCHAR(20),
  `Characteristic` VARCHAR(24),
  `Class` VARCHAR(16),
  `InspectionType` VARCHAR(18),
  `Specification` VARCHAR(48),
  `Method` VARCHAR(24),
  `Equipment` VARCHAR(36),
  `Standard` VARCHAR(20),
  `ISOLevel` VARCHAR(16),
  `AQL` DOUBLE,
  `Frequency` VARCHAR(28),
  `LotSize` VARCHAR(18),
  `ISOCode` VARCHAR(16),
  `SampleSize` VARCHAR(16),
  `AcceptanceNumber` VARCHAR(20),
  `RejectionNumber` VARCHAR(20),
  `Owner` VARCHAR(20),
  `ReactionPlan` VARCHAR(44)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_bottle` (
  `ProductId` VARCHAR(40),
  `ProductType` VARCHAR(16),
  `MoldId` VARCHAR(18),
  `BaseMaterial` VARCHAR(16),
  `ColorId` VARCHAR(16),
  `ColorName` VARCHAR(38),
  `PantoneCodeApprox` VARCHAR(40),
  `MasterbatchType` VARCHAR(64),
  `StandardDosagePctMass` DOUBLE,
  `VolumeMl` BIGINT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_cap` (
  `CapId` VARCHAR(38),
  `ItemDescription` VARCHAR(62),
  `OpeningType` VARCHAR(18),
  `MoldId` VARCHAR(18),
  `OuterDiameterMm` BIGINT,
  `HeightMm` BIGINT,
  `Material` VARCHAR(16),
  `MinWeightG` DOUBLE,
  `MaxWeightG` DOUBLE,
  `MinThicknessMm` DOUBLE,
  `MaxThicknessMm` DOUBLE,
  `ThreadType` VARCHAR(20),
  `ThreadDiameterMm` BIGINT,
  `FiodaRosca` BIGINT,
  `ThreadFinish` VARCHAR(16)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_ink` (
  `PrintToolId` VARCHAR(52),
  `ProductId` VARCHAR(40),
  `ColorCount` DOUBLE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_machine` (
  `MachineId` VARCHAR(16),
  `Process` VARCHAR(34),
  `MachineNumber` BIGINT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_mold` (
  `MoldId` VARCHAR(52),
  `MachineId` VARCHAR(16),
  `Process` VARCHAR(34),
  `Cavities` DOUBLE,
  `RatedCapacityPerHour` VARCHAR(28),
  `CyclesPerHour` DOUBLE,
  `IdealCycleTimeSec` DOUBLE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_operator` (
  `PersonId` VARCHAR(46),
  `Process` VARCHAR(34),
  `Role` VARCHAR(22)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_customer` (
  `CustomerId` VARCHAR(16),
  `CustomerName` VARCHAR(60),
  `City` VARCHAR(40),
  `Segment` VARCHAR(32),
  `CustomerTier` VARCHAR(16),
  `State` VARCHAR(16),
  `Country` VARCHAR(16),
  `Region` VARCHAR(52)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_supplier` (
  `SupplierId` VARCHAR(16),
  `SupplierName` VARCHAR(56),
  `Country` VARCHAR(28),
  `HeadquartersCity` VARCHAR(26),
  `MaterialsSupplied` VARCHAR(32),
  `SupplierTier` VARCHAR(16),
  `YearsAsSupplier` BIGINT,
  `ContractType` VARCHAR(40)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_raw_material_control_plan` (
  `Material` VARCHAR(22),
  `Characteristic` VARCHAR(60),
  `Standard` VARCHAR(78),
  `Method` VARCHAR(50),
  `Unit` VARCHAR(20),
  `LSL` DOUBLE,
  `Nominal` DOUBLE,
  `USL` DOUBLE,
  `InspectionType` VARCHAR(16),
  `Frequency` VARCHAR(32),
  `SampleSize` VARCHAR(20),
  `ReactionPlan` VARCHAR(56)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

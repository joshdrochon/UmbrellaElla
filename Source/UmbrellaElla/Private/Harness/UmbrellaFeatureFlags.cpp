#include "Harness/UmbrellaFeatureFlags.h"

namespace
{
	struct FFeatureDefault
	{
		EFeatureId Id;
		bool bEnabled;
	};

	constexpr FFeatureDefault FeatureDefaults[] = {
		{ EFeatureId::FLOW_02, true }, // bake: FLOW-02.enabled
		{ EFeatureId::FLOW_03, true }, // bake: FLOW-03.enabled
		{ EFeatureId::FLOW_04, true }, // bake: FLOW-04.enabled
		{ EFeatureId::MOVE_04, true }, // bake: MOVE-04.enabled
		{ EFeatureId::MOVE_05, true }, // bake: MOVE-05.enabled
		{ EFeatureId::MOVE_06, true }, // bake: MOVE-06.enabled
		{ EFeatureId::MOVE_07, true }, // bake: MOVE-07.enabled
		{ EFeatureId::MOVE_08, true }, // bake: MOVE-08.enabled
		{ EFeatureId::MOVE_09, true }, // bake: MOVE-09.enabled
		{ EFeatureId::MOVE_10, true }, // bake: MOVE-10.enabled
		{ EFeatureId::MOVE_11, true }, // bake: MOVE-11.enabled
		{ EFeatureId::MOVE_12, true }, // bake: MOVE-12.enabled
		{ EFeatureId::MOVE_13, true }, // bake: MOVE-13.enabled
		{ EFeatureId::MOVE_14, true }, // bake: MOVE-14.enabled
		{ EFeatureId::MOVE_15, true }, // bake: MOVE-15.enabled
		{ EFeatureId::MOVE_16, true }, // bake: MOVE-16.enabled
		{ EFeatureId::MOVE_17, true }, // bake: MOVE-17.enabled
		{ EFeatureId::MOVE_18, true }, // bake: MOVE-18.enabled
		{ EFeatureId::MOVE_19, true }, // bake: MOVE-19.enabled
		{ EFeatureId::MOVE_20, true }, // bake: MOVE-20.enabled
		{ EFeatureId::MOVE_21, true }, // bake: MOVE-21.enabled
		{ EFeatureId::SURV_05, true }, // bake: SURV-05.enabled
		{ EFeatureId::UMB_05, true }, // bake: UMB-05.enabled
		{ EFeatureId::WIND_03, true }, // bake: WIND-03.enabled
		{ EFeatureId::MOVE_22, true }, // bake: MOVE-22.enabled
		{ EFeatureId::COM_05, true }, // bake: COM-05.enabled
		{ EFeatureId::COM_06, true }, // bake: COM-06.enabled
		{ EFeatureId::COM_07, true }, // bake: COM-07.enabled
		{ EFeatureId::COM_08, true }, // bake: COM-08.enabled
		{ EFeatureId::COM_09, true }, // bake: COM-09.enabled
		{ EFeatureId::COM_10, true }, // bake: COM-10.enabled
		{ EFeatureId::COM_11, true }, // bake: COM-11.enabled
		{ EFeatureId::FLOW_05, true }, // bake: FLOW-05.enabled
		{ EFeatureId::FLOW_06, true }, // bake: FLOW-06.enabled
		{ EFeatureId::FLOW_07, true }, // bake: FLOW-07.enabled
		{ EFeatureId::FLOW_08, true }, // bake: FLOW-08.enabled
		{ EFeatureId::FLOW_09, true }, // bake: FLOW-09.enabled
		{ EFeatureId::FLOW_10, true }, // bake: FLOW-10.enabled
		{ EFeatureId::FLOW_11, true }, // bake: FLOW-11.enabled
		{ EFeatureId::FLOW_12, true }, // bake: FLOW-12.enabled
		{ EFeatureId::FLOW_13, true }, // bake: FLOW-13.enabled
		{ EFeatureId::FLOW_14, true }, // bake: FLOW-14.enabled
		{ EFeatureId::FLOW_15, true }, // bake: FLOW-15.enabled
		{ EFeatureId::FLOW_16, true }, // bake: FLOW-16.enabled
		{ EFeatureId::SURV_06, true }, // bake: SURV-06.enabled
		{ EFeatureId::SURV_07, true }, // bake: SURV-07.enabled
		{ EFeatureId::FLOW_17, true }, // bake: FLOW-17.enabled
		{ EFeatureId::FLOW_18, true }, // bake: FLOW-18.enabled
		{ EFeatureId::FLOW_19, true }, // bake: FLOW-19.enabled
		{ EFeatureId::FLOW_20, true }, // bake: FLOW-20.enabled
		{ EFeatureId::FLOW_21, true }, // bake: FLOW-21.enabled
		{ EFeatureId::FLOW_22, true }, // bake: FLOW-22.enabled
		{ EFeatureId::FLOW_23, true }, // bake: FLOW-23.enabled
		{ EFeatureId::OWL_06, true }, // bake: OWL-06.enabled
		{ EFeatureId::OWL_07, true }, // bake: OWL-07.enabled
		{ EFeatureId::OWL_08, true }, // bake: OWL-08.enabled
		{ EFeatureId::OWL_09, true }, // bake: OWL-09.enabled
		{ EFeatureId::OWL_10, true }, // bake: OWL-10.enabled
		{ EFeatureId::OWL_11, true }, // bake: OWL-11.enabled
		{ EFeatureId::OWL_12, true }, // bake: OWL-12.enabled
		{ EFeatureId::OWL_13, true }, // bake: OWL-13.enabled
		{ EFeatureId::OWL_14, true }, // bake: OWL-14.enabled
		{ EFeatureId::OWL_15, true }, // bake: OWL-15.enabled
		{ EFeatureId::OWL_16, true }, // bake: OWL-16.enabled
		{ EFeatureId::OWL_17, true }, // bake: OWL-17.enabled
		{ EFeatureId::OWL_18, true }, // bake: OWL-18.enabled
		{ EFeatureId::OWL_19, true }, // bake: OWL-19.enabled
		{ EFeatureId::OWL_20, true }, // bake: OWL-20.enabled
		{ EFeatureId::OWL_21, true }, // bake: OWL-21.enabled
		{ EFeatureId::OWL_22, true }, // bake: OWL-22.enabled
		{ EFeatureId::OWL_23, true }, // bake: OWL-23.enabled
		{ EFeatureId::OWL_24, true }, // bake: OWL-24.enabled
		{ EFeatureId::OWL_25, true }, // bake: OWL-25.enabled
		{ EFeatureId::OWL_26, true }, // bake: OWL-26.enabled
		{ EFeatureId::OWL_27, true }, // bake: OWL-27.enabled
		{ EFeatureId::OWL_28, true }, // bake: OWL-28.enabled
		{ EFeatureId::OWL_29, true }, // bake: OWL-29.enabled
		{ EFeatureId::OWL_30, true }, // bake: OWL-30.enabled
		{ EFeatureId::OWL_31, true }, // bake: OWL-31.enabled
		{ EFeatureId::OWL_32, true }, // bake: OWL-32.enabled
		{ EFeatureId::OWL_33, true }, // bake: OWL-33.enabled
		{ EFeatureId::OWL_34, true }, // bake: OWL-34.enabled
		{ EFeatureId::OWL_35, true }, // bake: OWL-35.enabled
		{ EFeatureId::FLOW_24, true }, // bake: FLOW-24.enabled
		{ EFeatureId::FLOW_25, true }, // bake: FLOW-25.enabled
		{ EFeatureId::FLOW_26, true }, // bake: FLOW-26.enabled
		{ EFeatureId::HAZ_02, true }, // bake: HAZ-02.enabled
		{ EFeatureId::HAZ_03, true }, // bake: HAZ-03.enabled
		{ EFeatureId::HAZ_04, true }, // bake: HAZ-04.enabled
		{ EFeatureId::HAZ_05, true }, // bake: HAZ-05.enabled
		{ EFeatureId::HAZ_06, true }, // bake: HAZ-06.enabled
		{ EFeatureId::HAZ_07, true }, // bake: HAZ-07.enabled
		{ EFeatureId::HAZ_08, true }, // bake: HAZ-08.enabled
		{ EFeatureId::HAZ_09, true }, // bake: HAZ-09.enabled
		{ EFeatureId::HAZ_10, true }, // bake: HAZ-10.enabled
		{ EFeatureId::HAZ_11, true }, // bake: HAZ-11.enabled
		{ EFeatureId::HAZ_12, true }, // bake: HAZ-12.enabled
		{ EFeatureId::HAZ_13, true }, // bake: HAZ-13.enabled
		{ EFeatureId::HAZ_14, true }, // bake: HAZ-14.enabled
		{ EFeatureId::HAZ_15, true }, // bake: HAZ-15.enabled
		{ EFeatureId::HAZ_16, true }, // bake: HAZ-16.enabled
		{ EFeatureId::HAZ_17, true }, // bake: HAZ-17.enabled
		{ EFeatureId::HAZ_18, true }, // bake: HAZ-18.enabled
		{ EFeatureId::CAM_03, true }, // bake: CAM-03.enabled
		{ EFeatureId::CAM_04, true }, // bake: CAM-04.enabled
		{ EFeatureId::CAM_05, true }, // bake: CAM-05.enabled
		{ EFeatureId::CAM_06, true }, // bake: CAM-06.enabled
		{ EFeatureId::CAM_07, true }, // bake: CAM-07.enabled
		{ EFeatureId::CAM_08, true }, // bake: CAM-08.enabled
		{ EFeatureId::HAZ_19, true }, // bake: HAZ-19.enabled
		{ EFeatureId::HAZ_20, true }, // bake: HAZ-20.enabled
		{ EFeatureId::HAZ_21, true }, // bake: HAZ-21.enabled
		{ EFeatureId::HAZ_22, true }, // bake: HAZ-22.enabled
		{ EFeatureId::HAZ_23, true }, // bake: HAZ-23.enabled
		{ EFeatureId::COM_12, true }, // bake: COM-12.enabled
		{ EFeatureId::COM_13, true }, // bake: COM-13.enabled
		{ EFeatureId::FLOW_46, true }, // bake: FLOW-46.enabled
		{ EFeatureId::HAZ_41, true }, // bake: HAZ-41.enabled
		{ EFeatureId::FLOW_47, true }, // bake: FLOW-47.enabled
		{ EFeatureId::COM_14, true }, // bake: COM-14.enabled
		{ EFeatureId::COM_15, true }, // bake: COM-15.enabled
		{ EFeatureId::COM_16, true }, // bake: COM-16.enabled
		{ EFeatureId::COM_17, true }, // bake: COM-17.enabled
		{ EFeatureId::COM_18, true }, // bake: COM-18.enabled
		{ EFeatureId::HAZ_24, true }, // bake: HAZ-24.enabled
		{ EFeatureId::HAZ_25, true }, // bake: HAZ-25.enabled
		{ EFeatureId::HAZ_26, true }, // bake: HAZ-26.enabled
		{ EFeatureId::HAZ_27, true }, // bake: HAZ-27.enabled
		{ EFeatureId::HAZ_28, true }, // bake: HAZ-28.enabled
		{ EFeatureId::HAZ_29, true }, // bake: HAZ-29.enabled
		{ EFeatureId::HAZ_30, true }, // bake: HAZ-30.enabled
		{ EFeatureId::HAZ_31, true }, // bake: HAZ-31.enabled
		{ EFeatureId::HAZ_32, true }, // bake: HAZ-32.enabled
		{ EFeatureId::HAZ_33, true }, // bake: HAZ-33.enabled
		{ EFeatureId::HAZ_34, true }, // bake: HAZ-34.enabled
		{ EFeatureId::HAZ_35, true }, // bake: HAZ-35.enabled
		{ EFeatureId::HAZ_36, true }, // bake: HAZ-36.enabled
		{ EFeatureId::HAZ_37, true }, // bake: HAZ-37.enabled
		{ EFeatureId::HAZ_38, true }, // bake: HAZ-38.enabled
		{ EFeatureId::HAZ_39, true }, // bake: HAZ-39.enabled
		{ EFeatureId::HAZ_40, true }, // bake: HAZ-40.enabled
		{ EFeatureId::FLOW_27, true }, // bake: FLOW-27.enabled
		{ EFeatureId::FLOW_28, true }, // bake: FLOW-28.enabled
		{ EFeatureId::FLOW_29, true }, // bake: FLOW-29.enabled
		{ EFeatureId::NAR_02, true }, // bake: NAR-02.enabled
		{ EFeatureId::NAR_03, true }, // bake: NAR-03.enabled
		{ EFeatureId::NAR_04, true }, // bake: NAR-04.enabled
		{ EFeatureId::NAR_05, true }, // bake: NAR-05.enabled
		{ EFeatureId::NAR_06, true }, // bake: NAR-06.enabled
		{ EFeatureId::NAR_07, true }, // bake: NAR-07.enabled
		{ EFeatureId::NAR_08, true }, // bake: NAR-08.enabled
		{ EFeatureId::FLOW_30, true }, // bake: FLOW-30.enabled
		{ EFeatureId::FLOW_48, true }, // bake: FLOW-48.enabled
		{ EFeatureId::FLOW_31, true }, // bake: FLOW-31.enabled
		{ EFeatureId::FLOW_32, true }, // bake: FLOW-32.enabled
		{ EFeatureId::FLOW_33, true }, // bake: FLOW-33.enabled
		{ EFeatureId::FLOW_34, true }, // bake: FLOW-34.enabled
		{ EFeatureId::FLOW_35, true }, // bake: FLOW-35.enabled
		{ EFeatureId::FLOW_36, true }, // bake: FLOW-36.enabled
		{ EFeatureId::FLOW_37, true }, // bake: FLOW-37.enabled
		{ EFeatureId::FLOW_38, true }, // bake: FLOW-38.enabled
		{ EFeatureId::FLOW_39, true }, // bake: FLOW-39.enabled
		{ EFeatureId::FLOW_40, true }, // bake: FLOW-40.enabled
		{ EFeatureId::FLOW_49, true }, // bake: FLOW-49.enabled
		{ EFeatureId::FLOW_41, true }, // bake: FLOW-41.enabled
		{ EFeatureId::FLOW_42, true }, // bake: FLOW-42.enabled
		{ EFeatureId::FLOW_43, true }, // bake: FLOW-43.enabled
		{ EFeatureId::FLOW_44, true }, // bake: FLOW-44.enabled
		{ EFeatureId::FLOW_45, true }, // bake: FLOW-45.enabled
		{ EFeatureId::ART_03, true }, // bake: ART-03.enabled
		{ EFeatureId::ART_04, true }, // bake: ART-04.enabled
		{ EFeatureId::ART_05, true }, // bake: ART-05.enabled
		{ EFeatureId::ART_06, true }, // bake: ART-06.enabled
		{ EFeatureId::ART_07, true }, // bake: ART-07.enabled
		{ EFeatureId::ANIM_02, true }, // bake: ANIM-02.enabled
		{ EFeatureId::ANIM_03, true }, // bake: ANIM-03.enabled
		{ EFeatureId::ANIM_04, true }, // bake: ANIM-04.enabled
		{ EFeatureId::ANIM_05, true }, // bake: ANIM-05.enabled
		{ EFeatureId::ANIM_06, true }, // bake: ANIM-06.enabled
		{ EFeatureId::ANIM_07, true }, // bake: ANIM-07.enabled
		{ EFeatureId::ANIM_08, true }, // bake: ANIM-08.enabled
		{ EFeatureId::ART_08, true }, // bake: ART-08.enabled
		{ EFeatureId::ART_09, true }, // bake: ART-09.enabled
		{ EFeatureId::ANIM_09, true }, // bake: ANIM-09.enabled
		{ EFeatureId::ANIM_10, true }, // bake: ANIM-10.enabled
		{ EFeatureId::ART_10, true }, // bake: ART-10.enabled
		{ EFeatureId::BG_02, true }, // bake: BG-02.enabled
		{ EFeatureId::BG_03, true }, // bake: BG-03.enabled
		{ EFeatureId::BG_04, true }, // bake: BG-04.enabled
		{ EFeatureId::BG_05, true }, // bake: BG-05.enabled
		{ EFeatureId::BG_06, true }, // bake: BG-06.enabled
		{ EFeatureId::VFX_02, true }, // bake: VFX-02.enabled
		{ EFeatureId::VFX_03, true }, // bake: VFX-03.enabled
		{ EFeatureId::VFX_04, true }, // bake: VFX-04.enabled
		{ EFeatureId::VFX_05, true }, // bake: VFX-05.enabled
		{ EFeatureId::VFX_06, true }, // bake: VFX-06.enabled
		{ EFeatureId::VFX_07, true }, // bake: VFX-07.enabled
		{ EFeatureId::VFX_08, true }, // bake: VFX-08.enabled
		{ EFeatureId::VFX_09, true }, // bake: VFX-09.enabled
		{ EFeatureId::VFX_10, true }, // bake: VFX-10.enabled
		{ EFeatureId::VFX_11, true }, // bake: VFX-11.enabled
		{ EFeatureId::CORE_04, true }, // bake: CORE-04.enabled
		{ EFeatureId::CORE_05, true }, // bake: CORE-05.enabled
		{ EFeatureId::CORE_06, true }, // bake: CORE-06.enabled
	};

	const TCHAR* const GFeatureRuleIds[] = {
		TEXT("FLOW-02"),
		TEXT("FLOW-03"),
		TEXT("FLOW-04"),
		TEXT("MOVE-04"),
		TEXT("MOVE-05"),
		TEXT("MOVE-06"),
		TEXT("MOVE-07"),
		TEXT("MOVE-08"),
		TEXT("MOVE-09"),
		TEXT("MOVE-10"),
		TEXT("MOVE-11"),
		TEXT("MOVE-12"),
		TEXT("MOVE-13"),
		TEXT("MOVE-14"),
		TEXT("MOVE-15"),
		TEXT("MOVE-16"),
		TEXT("MOVE-17"),
		TEXT("MOVE-18"),
		TEXT("MOVE-19"),
		TEXT("MOVE-20"),
		TEXT("MOVE-21"),
		TEXT("SURV-05"),
		TEXT("UMB-05"),
		TEXT("WIND-03"),
		TEXT("MOVE-22"),
		TEXT("COM-05"),
		TEXT("COM-06"),
		TEXT("COM-07"),
		TEXT("COM-08"),
		TEXT("COM-09"),
		TEXT("COM-10"),
		TEXT("COM-11"),
		TEXT("FLOW-05"),
		TEXT("FLOW-06"),
		TEXT("FLOW-07"),
		TEXT("FLOW-08"),
		TEXT("FLOW-09"),
		TEXT("FLOW-10"),
		TEXT("FLOW-11"),
		TEXT("FLOW-12"),
		TEXT("FLOW-13"),
		TEXT("FLOW-14"),
		TEXT("FLOW-15"),
		TEXT("FLOW-16"),
		TEXT("SURV-06"),
		TEXT("SURV-07"),
		TEXT("FLOW-17"),
		TEXT("FLOW-18"),
		TEXT("FLOW-19"),
		TEXT("FLOW-20"),
		TEXT("FLOW-21"),
		TEXT("FLOW-22"),
		TEXT("FLOW-23"),
		TEXT("OWL-06"),
		TEXT("OWL-07"),
		TEXT("OWL-08"),
		TEXT("OWL-09"),
		TEXT("OWL-10"),
		TEXT("OWL-11"),
		TEXT("OWL-12"),
		TEXT("OWL-13"),
		TEXT("OWL-14"),
		TEXT("OWL-15"),
		TEXT("OWL-16"),
		TEXT("OWL-17"),
		TEXT("OWL-18"),
		TEXT("OWL-19"),
		TEXT("OWL-20"),
		TEXT("OWL-21"),
		TEXT("OWL-22"),
		TEXT("OWL-23"),
		TEXT("OWL-24"),
		TEXT("OWL-25"),
		TEXT("OWL-26"),
		TEXT("OWL-27"),
		TEXT("OWL-28"),
		TEXT("OWL-29"),
		TEXT("OWL-30"),
		TEXT("OWL-31"),
		TEXT("OWL-32"),
		TEXT("OWL-33"),
		TEXT("OWL-34"),
		TEXT("OWL-35"),
		TEXT("FLOW-24"),
		TEXT("FLOW-25"),
		TEXT("FLOW-26"),
		TEXT("HAZ-02"),
		TEXT("HAZ-03"),
		TEXT("HAZ-04"),
		TEXT("HAZ-05"),
		TEXT("HAZ-06"),
		TEXT("HAZ-07"),
		TEXT("HAZ-08"),
		TEXT("HAZ-09"),
		TEXT("HAZ-10"),
		TEXT("HAZ-11"),
		TEXT("HAZ-12"),
		TEXT("HAZ-13"),
		TEXT("HAZ-14"),
		TEXT("HAZ-15"),
		TEXT("HAZ-16"),
		TEXT("HAZ-17"),
		TEXT("HAZ-18"),
		TEXT("CAM-03"),
		TEXT("CAM-04"),
		TEXT("CAM-05"),
		TEXT("CAM-06"),
		TEXT("CAM-07"),
		TEXT("CAM-08"),
		TEXT("HAZ-19"),
		TEXT("HAZ-20"),
		TEXT("HAZ-21"),
		TEXT("HAZ-22"),
		TEXT("HAZ-23"),
		TEXT("COM-12"),
		TEXT("COM-13"),
		TEXT("FLOW-46"),
		TEXT("HAZ-41"),
		TEXT("FLOW-47"),
		TEXT("COM-14"),
		TEXT("COM-15"),
		TEXT("COM-16"),
		TEXT("COM-17"),
		TEXT("COM-18"),
		TEXT("HAZ-24"),
		TEXT("HAZ-25"),
		TEXT("HAZ-26"),
		TEXT("HAZ-27"),
		TEXT("HAZ-28"),
		TEXT("HAZ-29"),
		TEXT("HAZ-30"),
		TEXT("HAZ-31"),
		TEXT("HAZ-32"),
		TEXT("HAZ-33"),
		TEXT("HAZ-34"),
		TEXT("HAZ-35"),
		TEXT("HAZ-36"),
		TEXT("HAZ-37"),
		TEXT("HAZ-38"),
		TEXT("HAZ-39"),
		TEXT("HAZ-40"),
		TEXT("FLOW-27"),
		TEXT("FLOW-28"),
		TEXT("FLOW-29"),
		TEXT("NAR-02"),
		TEXT("NAR-03"),
		TEXT("NAR-04"),
		TEXT("NAR-05"),
		TEXT("NAR-06"),
		TEXT("NAR-07"),
		TEXT("NAR-08"),
		TEXT("FLOW-30"),
		TEXT("FLOW-48"),
		TEXT("FLOW-31"),
		TEXT("FLOW-32"),
		TEXT("FLOW-33"),
		TEXT("FLOW-34"),
		TEXT("FLOW-35"),
		TEXT("FLOW-36"),
		TEXT("FLOW-37"),
		TEXT("FLOW-38"),
		TEXT("FLOW-39"),
		TEXT("FLOW-40"),
		TEXT("FLOW-49"),
		TEXT("FLOW-41"),
		TEXT("FLOW-42"),
		TEXT("FLOW-43"),
		TEXT("FLOW-44"),
		TEXT("FLOW-45"),
		TEXT("ART-03"),
		TEXT("ART-04"),
		TEXT("ART-05"),
		TEXT("ART-06"),
		TEXT("ART-07"),
		TEXT("ANIM-02"),
		TEXT("ANIM-03"),
		TEXT("ANIM-04"),
		TEXT("ANIM-05"),
		TEXT("ANIM-06"),
		TEXT("ANIM-07"),
		TEXT("ANIM-08"),
		TEXT("ART-08"),
		TEXT("ART-09"),
		TEXT("ANIM-09"),
		TEXT("ANIM-10"),
		TEXT("ART-10"),
		TEXT("BG-02"),
		TEXT("BG-03"),
		TEXT("BG-04"),
		TEXT("BG-05"),
		TEXT("BG-06"),
		TEXT("VFX-02"),
		TEXT("VFX-03"),
		TEXT("VFX-04"),
		TEXT("VFX-05"),
		TEXT("VFX-06"),
		TEXT("VFX-07"),
		TEXT("VFX-08"),
		TEXT("VFX-09"),
		TEXT("VFX-10"),
		TEXT("VFX-11"),
		TEXT("CORE-04"),
		TEXT("CORE-05"),
		TEXT("CORE-06")
	};

	static_assert(UE_ARRAY_COUNT(FeatureDefaults) == static_cast<int32>(EFeatureId::Count), "flag table out of sync with the manifest");
}

bool IsFeatureEnabled(EFeatureId Id)
{
	const int32 Index = static_cast<int32>(Id);
	return Index >= 0 && Index < static_cast<int32>(EFeatureId::Count) && FeatureDefaults[Index].bEnabled;
}

const TCHAR* GetFeatureManifestVersion()
{
	return TEXT("SH1.0-m1");
}

const TCHAR* GetFeatureRuleId(EFeatureId Id)
{
	const int32 Index = static_cast<int32>(Id);
	return (Index >= 0 && Index < static_cast<int32>(EFeatureId::Count)) ? GFeatureRuleIds[Index] : TEXT("none");
}

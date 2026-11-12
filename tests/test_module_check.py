"""Tests for tools/module_check.py (Technical Director's module-boundary gate).

tests/fixtures/modules/clean is a two-module Source/ tree that follows pipeline/unreal-rules.md.
Each broken_<rule>_* fixture is the clean tree with one rule broken on purpose. Every broken
fixture must be caught by exactly its own rule, and the clean tree must produce nothing."""
import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import module_check  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "modules")

# fixture -> (rule letter, number of findings expected)
BROKEN = {
    "broken_a_private_include": ("a", 2),            # one relative "../" include, one "Module/Private/..." include
    "broken_b_missing_dep": ("b", 2),                # project module and Paper2D-style engine module
    "broken_c_public_exposes_private_dep": ("c", 2),  # by include and by forward-declared type name
    "broken_d_missing_api": ("d", 1),
    "broken_e_generated_not_last": ("e", 1),
    "broken_f_raw_uobject": ("f", 4),                # two plain members, one TArray<U*>, one TMap<FName, A*>
    "broken_g_iwyu": ("g", 1),
}


H = "Source/UmbrellaElla/Public/Umbrella/UmbrellaComponent.h"
CPP = "Source/UmbrellaElla/Private/Umbrella/UmbrellaComponent.cpp"
CHAR_CPP = "Source/UmbrellaElla/Private/Character/EllaCharacter.cpp"
TICK_END = "\tUObject* Scratch = nullptr; // locals are fine\n"
INCLUDES_END = '#include "PaperFlipbook.h"\n'

# Rules h-v (C++ standard): rule -> (expected count, [(file, old text in clean, new text)]).
# Each one breaks the clean tree on purpose; only that rule may fire.
STYLE_CASES = {
    "h": (1, [(H, "#pragma once\n", "")]),
    "i": (1, [(CPP, "UObject* Scratch = nullptr;", "UObject* Scratch = NULL;")]),
    "j": (4, [(CPP, INCLUDES_END, INCLUDES_END + "#include <vector>\n"),
              (CPP, TICK_END, TICK_END + "\tstd::vector<int> V;\n\tAActor* Owner2 = dynamic_cast<AActor*>(GetOwner());\n"
                              "\tthrow 1;\n")]),
    "k": (1, [(CPP, TICK_END, TICK_END + '\tUE_LOG(LogTemp, Log, TEXT("tick"));\n')]),
    "l": (2, [(CPP, INCLUDES_END, INCLUDES_END + "\nusing namespace UE;\n"),
              (CPP, "using namespace UE;\n", "using namespace UE;\nusing FMath::Max;\n")]),
    "m": (1, [(H, "FActorComponentTickFunction* ThisTickFunction) override;", "FActorComponentTickFunction* ThisTickFunction);")]),
    "n": (3, [(H, "bool bOpen = false;", "bool Open = false;\n\tUPROPERTY()\n\tuint8 Flying : 1;"),
              (H, "void SetOpen(bool bNewOpen);", "void SetOpen(bool NewOpen);")]),
    "o": (1, [(H, "bool IsOpen() const", "bool Opened() const")]),
    "p": (2, [(CPP, "\tbOpen = bNewOpen;\n", "\tif (bNewOpen)\n\t\tbOpen = true;\n\telse\n\t\tbOpen = false;\n")]),
    "q": (1, [(CPP, TICK_END, TICK_END + "\tswitch (TickType)\n\t{\n\tcase LEVELTICK_All:\n\t\tbreak;\n\t}\n")]),
    "r": (3, [(CPP, TICK_END, TICK_END + '\tUE_LOG(LogUmbrellaElla, Log, "tick %f", DeltaTime);\n\tFString Label = "Umbrella";\n'),
              (CHAR_CPP, '(TEXT("Umbrella"))', '("Umbrella")')]),
    "s": (2, [(CPP, INCLUDES_END, INCLUDES_END + '\nstatic TAutoConsoleVariable<int32> CVarUmbrellaDebug(TEXT("ue.Debug"), 0, TEXT("Umbrella debug"));\n'),
              (H, "\tbool IsOpen() const", "\tUFUNCTION(Exec)\n\tvoid UmbrellaGod();\n\n\tbool IsOpen() const")]),
    "t": (1, [(H, "\tGENERATED_BODY()", "    GENERATED_BODY()"), (H, "\tUUmbrellaComponent();", "    UUmbrellaComponent();")]),
    "u": (1, [(CPP, TICK_END, TICK_END + "\tif (GetWorld()->GetFirstPlayerController()->IsInputKeyDown(EKeys::SpaceBar))\n\t{\n\t\tbOpen = true;\n\t}\n")]),
    # a literal true, and a loop flag held in a variable (object form and delegate form)
    "v": (3, [(CPP, "\tbOpen = bNewOpen;\n", "\tbOpen = bNewOpen;\n\tGetWorld()->GetTimerManager().SetTimer(BlinkHandle, this, &UUmbrellaComponent::Blink, 0.5f, true);\n"
                                         "\tGetWorld()->GetTimerManager().SetTimer(BlinkHandle, this, &UUmbrellaComponent::Blink, 0.5f, bNewOpen);\n"
                                         "\tGetWorld()->GetTimerManager().SetTimer(BlinkHandle, FTimerDelegate::CreateUObject(this, &UUmbrellaComponent::Blink), 0.5f, bNewOpen);\n")]),
}

PRIV_END = "\tbool bOpen = false;\n"
PROT_END = "\tTObjectPtr<UPaperFlipbook> OpenFlipbook;\n"
SHELL_END = '\tUmbrella = CreateDefaultSubobject<UUmbrellaComponent>(TEXT("Umbrella"));\n}\n'
PUB_END = "\tbool IsOpen() const { return bOpen; }\n"
FWD = "class UPaperFlipbook;\n"
# Rules w-z and A-H (more of Epic's standard), same shape as STYLE_CASES.
STANDARD_CASES = {
    "w": (6, [(H, FWD, FWD + "\nUCLASS()\nclass UMBRELLAELLA_API WindThing : public UObject\n{\n\tGENERATED_BODY()\n};\n"
                          "\nUCLASS()\nclass UMBRELLAELLA_API UWindActor : public AActor\n{\n\tGENERATED_BODY()\n};\n"
                          "\nstruct UMBRELLAELLA_API WindData\n{\n};\n\nenum class umbrellaMode : uint8\n{\n\tOpen\n};\n"),
              (H, PRIV_END, PRIV_END + "\tfloat speed_value = 0.f;\n\tvoid doThing();\n")]),
    # locals and parameters, in .cpp and .h
    "w_locals": (3, [(CPP, TICK_END, TICK_END + "\tfloat my_local = DeltaTime;\n\tfor (int32 index : TArray<int32>())\n\t{\n\t}\n"),
                     (H, PUB_END, PUB_END + "\tvoid Push(float push_speed);\n")]),
    "x": (3, [(CPP, TICK_END, TICK_END + "\tfloat Local = 0.f;\n\tFTimerHandle H2;\n"
                                         "\tGetWorld()->GetTimerManager().SetTimer(H2, [&]() { Local += 1.f; }, 0.5f, false);\n"
                                         "\tGetWorld()->GetTimerManager().SetTimer(H2, FTimerDelegate::CreateLambda([this, &Local]() "
                                         "{ bOpen = true; }), 0.5f, false);\n")]),
    # a lambda stored in a variable first, then passed to SetTimer / CreateLambda
    "x_stored": (2, [(CPP, TICK_END, TICK_END + "\tfloat Local = 0.f;\n\tFTimerHandle H3;\n"
                                                "\tauto Later = [&Local]() { Local += 1.f; };\n"
                                                "\tauto Again = [this]() { bOpen = true; };\n"
                                                "\tGetWorld()->GetTimerManager().SetTimer(H3, Later, 0.5f, false);\n"
                                                "\tGetWorld()->GetTimerManager().SetTimer(H3, FTimerDelegate::CreateLambda(Again), 0.5f, false);\n")]),
    "y": (1, [(CPP, TICK_END, TICK_END + "\tauto Owner3 = GetOwner();\n")]),
    "z": (2, [(H, FWD, FWD + "\nUENUM(BlueprintType)\nenum EUmbrellaState\n{\n\tClosed,\n\tOpened\n};\n"
                          "\nUENUM()\nenum class EUmbrellaMode : int32\n{\n\tA\n};\n")]),
    "A": (1, [(H, PUB_END, PUB_END + "\tfloat GetSpeed() { return 0.f; }\n")]),
    "B": (1, [(H, PUB_END, PUB_END + "\tconst FVector GetWind() const;\n")]),
    "C": (3, [(H, PUB_END, PUB_END + "\tbool bPublicState = false;\n\tfloat Speed = 0.f;\n"
                                     "\tUPROPERTY(BlueprintReadWrite)\n\tfloat CurrentHealth = 0.f;\n")]),
    "D": (1, [(H, PUB_END, PUB_END + "\tvoid Absorb(UObject& Thing);\n")]),
    "E": (1, [(CPP, INCLUDES_END, INCLUDES_END + "#define DEBUG_ON 1\n")]),
    "F": (1, [(CPP, TICK_END, TICK_END + "\tif (AActor* Owner = GetOwner())\n\t{\n"
                                         "\t\tOwner->OnDestroyed.AddDynamic(this, &UUmbrellaComponent::OnOwnerGone);\n\t}\n")]),
    # unnamed, a const local, and a namespace-scope constexpr (digit separators too)
    "G": (3, [(CPP, TICK_END, TICK_END + "\tfloat Fall = DeltaTime * 600.f;\n\tconst float Gravity = 980.f;\n"),
              (CPP, INCLUDES_END, INCLUDES_END + "\nstatic constexpr int32 Big = 1'000'000;\n")]),
    "H": (1, [(CPP, TICK_END, TICK_END + "\tconst float StickDeadZone = DeltaTime;\n")]),
    "J": (2, [(H, PUB_END, PUB_END + "\tvoid Move(bool bFast);\n\tvoid Fire(float Power, bool bCharged = false);\n")]),
    # Coverage-map ports (docs/coverage-map.md): unrepeatable runs, state that survives PIE, writable container getters
    "N": (3, [(CPP, TICK_END, TICK_END + "\tfloat Jitter = FMath::FRand();\n\tdouble Started = FPlatformTime::Seconds();\n"
                                         "\tFDateTime When = FDateTime::Now();\n")]),
    "O": (2, [(CPP, INCLUDES_END, INCLUDES_END + "\nstatic int32 OpenCount = 0;\n"),
              (CPP, TICK_END, TICK_END + "\tstatic float Accumulated;\n")]),
    "P": (2, [(H, PUB_END, PUB_END + "\tTArray<float>& Samples();\n\tTMap<FName, float>* FindTable();\n")]),
    # Gaps a critic planted that used to print 0 problems.
    # protected gameplay state (only tuning and asset refs may be protected; VisibleAnywhere is not tuning)
    "C_protected": (4, [(H, PROT_END, PROT_END + "\n\tfloat CurrentFallSpeed;\n\tbool bFalling;\n\tbool bRising;\n"
                                                "\tUPROPERTY(VisibleAnywhere)\n\tfloat Shown = 0.f;\n")]),
    # [=] captures this implicitly: inline in CreateLambda, and [=, Count] straight in SetTimer
    "x_copy": (2, [(CPP, TICK_END, TICK_END + "\tint32 Count = 0;\n"
                                             "\tGetWorld()->GetTimerManager().SetTimer(BlinkHandle, FTimerDelegate::CreateLambda([=]() "
                                             "{ bOpen = false; }), 0.5f, false);\n"
                                             "\tGetWorld()->GetTimerManager().SetTimer(BlinkHandle, [=, Count]() { bOpen = Count > 0; }, 0.5f, false);\n")]),
    # a plain enum and an unnamed enum, outside any UENUM
    "z_plain": (2, [(H, FWD, FWD + "\nenum EWindKind\n{\n\tCalm,\n\tGusty\n};\n\nenum\n{\n\tUnusedSlot\n};\n")]),
    # engine overlap and movement virtuals outside the first list, without override
    "m_engine": (2, [(H, PUB_END, PUB_END + "\tvirtual void NotifyActorBeginOverlap(AActor* OtherActor);\n\tvirtual void Falling();\n")]),
    # any literal outside TEXT(): a level name in OpenLevel, an asset path
    "r_any": (2, [(CPP, TICK_END, TICK_END + '\tUGameplayStatics::OpenLevel(this, "L_Graybox");\n'
                                            '\tFSoftObjectPath Path("/Game/UmbrellaElla/Maps/L_Graybox");\n')]),
    # logic in the character shell: a Tick, and a BindAction in SetupPlayerInputComponent
    "L": (2, [(CHAR_CPP, SHELL_END, SHELL_END + "\nvoid AEllaCharacter::Tick(float DeltaSeconds)\n{\n\tSuper::Tick(DeltaSeconds);\n"
                                               "\tSetActorLocation(GetActorLocation() + FVector::UpVector);\n}\n"
                                               "\nvoid AEllaCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)\n{\n"
                                               "\tSuper::SetupPlayerInputComponent(PlayerInputComponent);\n"
                                               "\tUEnhancedInputComponent* Input = CastChecked<UEnhancedInputComponent>(PlayerInputComponent);\n"
                                               "\tInput->BindAction(UmbrellaAction, ETriggerEvent::Started, this, &AEllaCharacter::Toggle);\n}\n")]),
}

# Correct forms of the critic's gaps. Added to the clean tree, they must give no finding.
CORRECT_PROTECTED = """
	UPROPERTY(EditAnywhere, Category = "Umbrella", meta = (Units = "cm/s", ClampMin = "0"))
	float MaxRiseSpeed = 600.f;

	UPROPERTY(EditInstanceOnly)
	TObjectPtr<AActor> PatrolEnd;

	UPROPERTY(EditDefaultsOnly)
	FUmbrellaFlightTuning Flight;

	FUmbrellaFlightTuning DefaultFlight;

	static constexpr int32 MaxCharges = 3;
"""
CORRECT_PRIVATE = "\tTFunction<void()> Pending;\n\tTFunctionRef<bool(int32)> Filter;\n\tTDelegate<void(float)> OnSpeed;\n"
CORRECT_PUBLIC = ("\tvirtual void NotifyHit(class UPrimitiveComponent* MyComp, AActor* Other, class UPrimitiveComponent* OtherComp, "
                  "bool bSelfMoved, FVector HitLocation, FVector HitNormal, FVector NormalImpulse, const FHitResult& Hit) override;\n"
                  "\tvirtual void NotifyActorEndOverlap(AActor* OtherActor) override;\n")
CORRECT_LITERALS_CPP = r"""
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FUmbrellaOpenTest, "UmbrellaElla.Umbrella.Open", EAutomationTestFlags::EditorContext)
static_assert(sizeof(int32) == sizeof(uint32), "int32 and uint32 match");
extern "C" void UmbrellaNoop();

enum class EWindKind : uint8
{
	Calm
};

void UUmbrellaComponent::Travel()
{
	UGameplayStatics::OpenLevel(this, TEXT("L_Graybox"));
	FSoftObjectPath Path(TEXT("/Game/UmbrellaElla/Maps/L_Graybox"));
	FText Label = LOCTEXT("UmbrellaLabel", "Umbrella");
	FText Other = NSLOCTEXT("Umbrella", "Other", "Other");
	GetWorld()->GetTimerManager().SetTimer(BlinkHandle, FTimerDelegate::CreateWeakLambda(this, [this, Path]() { bOpen = Path.IsNull(); }), 0.5f, false);
}
"""
CORRECT_SHELL_CPP = """
void AEllaCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Input = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
		{
			Input->AddMappingContext(DefaultMapping, 0);
		}
	}
	Umbrella->BindInput(CastChecked<UEnhancedInputComponent>(PlayerInputComponent));
}
"""

# Correct forms of the same rules. Added to the clean tree, they must give no finding.
CORRECT_CPP = r"""
#define LOCTEXT_NAMESPACE "UmbrellaComponent"
#define UMBRELLAELLA_DEBUG_DRAW 0
#if !UE_BUILD_SHIPPING
static TAutoConsoleVariable<int32> CVarUmbrellaDebug(TEXT("ue.Debug"), 0, TEXT("Umbrella debug"));
#endif

#if UE_BUILD_SHIPPING
#else
static FAutoConsoleVariableRef CVarUmbrellaDebugRef(TEXT("ue.DebugRef"), GDebugRef, TEXT("ref"));
#endif

void UUmbrellaComponent::Correct(const TArray<int32>& Values)
{
	bool bForce = Values.Num() > 2;
	// Comments may say NULL, std::vector, LogTemp, if (x) y; and IsInputKeyDown( freely.
	const TCHAR* Note = TEXT("strings may too: NULL std::map LogTemp if (x) y; switch (a) {}");
	if (bForce)
	{
		UE_LOG(LogUmbrellaElla, Log, TEXT("forced %s"), *FString::Printf(TEXT("%d"), Values.Num()));
	}
	else if (Values.Num() > 0)
	{
		FName Tag = FName(TEXT("Umbrella"));
	}
	else
	{
		FString Empty = TEXT("");
	}
	for (int32 Value : Values)
	{
		bool bPositive = Value > 0;
	}
	const int32 MaxCount = UUmbrellaComponent::MaxCharges;
	int32 Count = 0;
	do
	{
		++Count;
	} while (Count < MaxCount);
	switch (Count)
	{
	case MaxCount:
	{
		break;
	}
	default:
		break;
	}
	const TCHAR Quote = '"';
	GetWorld()->GetTimerManager().SetTimer(BlinkHandle, this, &UUmbrellaComponent::Blink, 0.5f, true);
	GetWorld()->GetTimerManager().SetTimer(OnceHandle, this, &UUmbrellaComponent::Blink, 0.5f, false);
	GetWorld()->GetTimerManager().SetTimer(OnceHandle, FTimerDelegate::CreateWeakLambda(this, [this]() { bOpen = false; }), 0.5f, false);
	GetWorld()->GetTimerManager().SetTimer(OnceHandle, [Count]() { UE_LOG(LogUmbrellaElla, Log, TEXT("%d"), Count); }, 0.5f, false);
	using FMath::Max;
	const float Gravity = GetDefault<UUmbrellaTuning>()->Umbrella.Gravity;
	TMap<FName, int32> Lookup;
	for (const auto& Pair : Lookup)
	{
		Count += Pair.Value;
	}
	auto OnDone = [this]() { bOpen = false; };
	auto Weak = [Count]() { UE_LOG(LogUmbrellaElla, Log, TEXT("%d"), Count); };
	GetWorld()->GetTimerManager().SetTimer(OnceHandle, Weak, 0.5f, false);
	GetWorld()->GetTimerManager().SetTimer(OnceHandle, this, &UUmbrellaComponent::Blink, 0.5f);
	GetWorld()->GetTimerManager().SetTimer(OnceHandle, this, &UUmbrellaComponent::Blink, 0.5f, false, 0.5f);
	GetWorld()->GetTimerManager().SetTimer(OnceHandle, FTimerDelegate::CreateUObject(this, &UUmbrellaComponent::Blink), 0.5f, false, 0.5f);
	float LocalSpeed = DeltaTime;
	uint8 PackedFlags = 0;
	if (AActor* Owner = GetOwner())
	{
		Owner->OnDestroyed.AddDynamic(this, &UUmbrellaComponent::OnOwnerGone);
	}
	Box = CreateDefaultSubobject<UBoxComponent>(TEXT("Box"));
	Box->OnComponentBeginOverlap.AddDynamic(this, &UUmbrellaComponent::OnBoxOverlap);
}

void UUmbrellaComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (AActor* Owner = GetOwner())
	{
		Owner->OnDestroyed.RemoveDynamic(this, &UUmbrellaComponent::OnOwnerGone);
	}
	GetWorld()->GetTimerManager().ClearTimer(BlinkHandle);
	Super::EndPlay(EndPlayReason);
}
"""
CORRECT_H = """	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) final;
	bool HasWind() const;
	bool CanAttack() const;
	bool ShouldBrake(float Speed) const;
	virtual bool CanEditChange(const FProperty* InProperty) const override;
	bool operator==(const FUmbrellaRules& Other) const;
	void Correct(const TArray<int32>& Values);
	void SetVisible(bool bNewVisible);
	void OnBoxOverlap(UPrimitiveComponent* Comp, AActor* Other, UPrimitiveComponent* OtherComp, int32 Index, bool bFromSweep, const FHitResult& Hit);
	virtual void SetActive(bool bNewActive, bool bReset = false) override;
	static float NextSpeed(float Current, bool bOpen);
	void ReadFound(bool& bOutFound) const;
	static UUmbrellaComponent* GetDefaultUmbrella();
	const FVector& GetWindRef() const;
	float GetSpeed() const { return 0.f; }
	void Absorb(UObject* Thing);
	void OnHit_Implementation();
	static constexpr int32 MaxCharges = 3;

	bool IsOpen() const"""


def run(root):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = module_check.main(["--root", root])
    return code, buf.getvalue()


class ModuleCheckTests(unittest.TestCase):
    def test_clean_tree_passes(self):
        self.assertEqual(module_check.check(os.path.join(FIX, "clean")), [])
        self.assertEqual(run(os.path.join(FIX, "clean"))[0], 0)

    def test_every_rule_has_a_broken_fixture(self):
        self.assertEqual(sorted(r for r, _ in BROKEN.values()), list("abcdefg"))
        self.assertEqual(sorted(STYLE_CASES), list("hijklmnopqrstuv"))
        self.assertEqual(sorted(k[0] for k in STANDARD_CASES), sorted("wwxxyzABCDEFGHJ" + "CxzmrL" + "NOP"))

    def test_each_standard_rule_is_caught_by_its_rule_only(self):
        for rule, (count, edits) in STANDARD_CASES.items():
            with self.subTest(rule=rule):
                tmp = self._copy_clean()
                for rel, old, new in edits:
                    self._edit(tmp, rel, old, new)
                problems = module_check.check(tmp)
                self.assertEqual([p[0] for p in problems], [rule[0]] * count, problems)
                self.assertEqual(run(tmp)[0], 1)

    def test_critic_planted_violations_are_all_caught(self):
        # The 13 violations the critic planted (plus one public member), which used to print 0 problems.
        problems = module_check.check(os.path.join(FIX, "broken_wz_epic_standard"))
        self.assertEqual(sorted(p[0] for p in problems), sorted("ABCDEGlwwwwxyzz"), problems)

    def test_header_including_what_it_could_forward_declare_is_caught(self):
        ella = "Source/UmbrellaElla/Public/Character/EllaCharacter.h"
        tmp = self._copy_clean()
        self._edit(tmp, ella, "class UUmbrellaComponent;\n", "")
        self._edit(tmp, ella, '#include "EllaCharacter.generated.h"',
                   '#include "Umbrella/UmbrellaComponent.h"\n#include "EllaCharacter.generated.h"')
        self.assertEqual([p[0] for p in module_check.check(tmp)], ["I"])

    def test_header_including_a_type_it_uses_by_value_passes(self):
        tmp = self._copy_clean()
        with open(os.path.join(tmp, "Source/UmbrellaElla/Public/Umbrella/UmbrellaFlightTuning.h"), "w") as f:
            f.write('#pragma once\n\n#include "CoreMinimal.h"\n#include "UmbrellaFlightTuning.generated.h"\n\n'
                    'USTRUCT()\nstruct UMBRELLAELLA_API FUmbrellaFlightTuning\n{\n\tGENERATED_BODY()\n\n'
                    '\tUPROPERTY(EditAnywhere, meta = (Units = "cm/s"))\n\tfloat MaxRiseSpeed = 600.f;\n};\n')
        self._edit(tmp, H, '#include "UmbrellaComponent.generated.h"',
                   '#include "Umbrella/UmbrellaFlightTuning.h"\n#include "UmbrellaComponent.generated.h"')
        self._edit(tmp, H, PRIV_END, PRIV_END + "\tFUmbrellaFlightTuning Flight;\n")
        self.assertEqual(module_check.check(tmp), [])

    def test_each_style_rule_is_caught_by_its_rule_only(self):
        for rule, (count, edits) in STYLE_CASES.items():
            with self.subTest(rule=rule):
                tmp = self._copy_clean()
                for rel, old, new in edits:
                    self._edit(tmp, rel, old, new)
                problems = module_check.check(tmp)
                self.assertEqual([p[0] for p in problems], [rule] * count, problems)
                code, out = run(tmp)
                self.assertEqual(code, 1, out)

    def test_correct_forms_of_style_rules_pass(self):
        tmp = self._copy_clean()
        self._edit(tmp, CPP, TICK_END + "}\n", TICK_END + "}\n" + CORRECT_CPP)
        self._edit(tmp, H, "\tbool IsOpen() const", CORRECT_H)
        self._edit(tmp, H, PRIV_END, PRIV_END + "\tUPROPERTY()\n\tuint8 bPacked : 1;\n")
        self._edit(tmp, H, FWD, FWD + "\nUENUM(BlueprintType)\nenum class EUmbrellaState : uint8\n{\n\tClosed,\n\tOpened\n};\n")
        self.assertEqual(module_check.check(tmp), [])

    def test_correct_forms_of_coverage_rules_pass(self):
        # N: a seeded stream and world time; a harness file may read the clock. O: static const/constexpr and static
        # functions. P: const& and by-value container getters.
        tmp = self._copy_clean()
        self._edit(tmp, CPP, TICK_END, TICK_END + "\tFRandomStream Stream(7);\n\tfloat Roll = Stream.FRand();\n"
                                                  "\tconst double Started = GetWorld()->GetTimeSeconds();\n")
        self._edit(tmp, H, PUB_END, PUB_END + "\tconst TArray<float>& Samples() const { return SampleList; }\n"
                                              "\tTArray<float> CopySamples() const { return SampleList; }\n"
                                              "\tstatic constexpr int32 MaxSamples = 4;\n\tstatic const FName& SlotName();\n")
        self._edit(tmp, H, PRIV_END, PRIV_END + "\tTArray<float> SampleList;\n")
        harness = os.path.join(tmp, "Source/UmbrellaElla/Private/Harness")
        os.makedirs(harness, exist_ok=True)
        with open(os.path.join(harness, "RunClock.cpp"), "w") as f:
            f.write('#include "Umbrella/UmbrellaComponent.h"\n\ndouble RunStartSeconds()\n{\n\treturn FPlatformTime::Seconds();\n}\n')
        self.assertEqual([p for p in module_check.check(tmp) if p[0] in "NOP"], [])

    def test_correct_forms_of_critic_gaps_pass(self):
        # protected tuning and asset refs, TFunction members (rule w), overrides of the new engine virtuals,
        # literals in TEXT/LOCTEXT/macros that take plain literals, and a shell that only wires.
        tmp = self._copy_clean()
        self._edit(tmp, H, PROT_END, PROT_END + CORRECT_PROTECTED)
        self._edit(tmp, H, PRIV_END, PRIV_END + CORRECT_PRIVATE)
        self._edit(tmp, H, PUB_END, PUB_END + CORRECT_PUBLIC)
        self._edit(tmp, CPP, TICK_END + "}\n", TICK_END + "}\n" + CORRECT_LITERALS_CPP)
        self._edit(tmp, CHAR_CPP, SHELL_END, SHELL_END + CORRECT_SHELL_CPP)
        self.assertEqual(module_check.check(tmp), [])

    def test_notify_hit_without_override_is_caught(self):
        # The critic's plant: only rule J fired (on bSelfMoved). Rule m must fire too.
        tmp = self._copy_clean()
        self._edit(tmp, H, PUB_END, PUB_END + CORRECT_PUBLIC.replace(") override;\n\tvirtual void NotifyActorEnd", ");\n\tvirtual void NotifyActorEnd"))
        self.assertEqual(sorted(p[0] for p in module_check.check(tmp)), ["J", "m"])

    def test_rule_k_runs_only_when_asked(self):
        tmp = self._copy_clean()
        self.assertEqual(module_check.check(tmp), [])
        code, out = self._run_rules(tmp, "K")
        self.assertEqual(code, 1, out)
        self.assertEqual(out.count("[K]"), 2, out)   # final-9 A M8: the AEllaCharacter actor inherits Blueprintable
        # final, Blueprintable, or a Blueprint child listed in docs/asset-changes/ each clear it
        self._edit(tmp, H, "class UMBRELLAELLA_API UUmbrellaComponent :", "class UMBRELLAELLA_API UUmbrellaComponent final :")
        self._edit(tmp, "Source/UmbrellaEllaEditor/Private/UmbrellaValidator.h", "UCLASS()", "UCLASS(Blueprintable)")
        os.makedirs(os.path.join(tmp, "docs", "asset-changes"))
        with open(os.path.join(tmp, "docs", "asset-changes", "1.2-BP_Ella.json"), "w") as f:
            f.write('{"class": "BP_Ella", "parent": "AEllaCharacter"}\n')
        code, out = self._run_rules(tmp, "K")
        self.assertEqual(code, 0, out)

    def _run_rules(self, root, rules):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = module_check.main(["--root", root, "--rules", rules])
        return code, buf.getvalue()

    def test_settings_class_may_have_public_config_members(self):
        # UUmbrellaTuning is read as GetDefault<UUmbrellaTuning>()->Attack.X, so its members are public (rule C).
        tmp = self._copy_clean()
        self._edit(tmp, H, FWD, FWD + "\nUCLASS(Config = Game, defaultconfig)\nclass UMBRELLAELLA_API UUmbrellaTuning : public UDeveloperSettings\n"
                                      "{\n\tGENERATED_BODY()\n\npublic:\n\tUPROPERTY(Config, EditAnywhere)\n\tFUmbrellaFlightTuning Umbrella;\n};\n")
        self.assertEqual(module_check.check(tmp), [])
        self._edit(tmp, H, "public UDeveloperSettings", "public UObject")
        self.assertEqual([p[0] for p in module_check.check(tmp)], ["C"])

    def test_lambda_stored_but_not_deferred_passes(self):
        tmp = self._copy_clean()
        self._edit(tmp, CPP, TICK_END, TICK_END + "\tfloat Local = 0.f;\n\tauto Add = [&Local]() { Local += 1.f; };\n\tAdd();\n")
        self.assertEqual(module_check.check(tmp), [])

    def test_rules_flag_filters_output(self):
        tmp = self._copy_clean()
        self._edit(tmp, H, "#pragma once\n", "")
        self._edit(tmp, CPP, "UObject* Scratch = nullptr;", "UObject* Scratch = NULL;")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = module_check.main(["--root", tmp, "--rules", "i"])
        self.assertEqual(code, 1)
        self.assertIn("[i]", buf.getvalue())
        self.assertNotIn("[h]", buf.getvalue())

    def test_double_slash_inside_string_is_not_a_comment(self):
        tmp = self._copy_clean()
        self._edit(tmp, CPP, TICK_END, TICK_END + '\tconst TCHAR* Url = TEXT("http://x"); UObject* Other = NULL;\n')
        self.assertEqual([p[0] for p in module_check.check(tmp)], ["i"])

    def test_each_broken_fixture_is_caught_by_its_rule_only(self):
        for name, (rule, count) in BROKEN.items():
            with self.subTest(fixture=name):
                problems = module_check.check(os.path.join(FIX, name))
                self.assertEqual([p[0] for p in problems], [rule] * count, problems)
                code, out = run(os.path.join(FIX, name))
                self.assertEqual(code, 1, out)

    def test_no_source_folder_is_a_skip(self):
        empty = tempfile.mkdtemp()
        try:
            code, out = run(empty)
            self.assertEqual(code, 2)
            self.assertIn("SKIP", out)
        finally:
            shutil.rmtree(empty)

    def test_this_repository_has_no_source_yet_or_is_clean(self):
        code, out = run(ROOT)
        self.assertIn(code, (0, 2), out)

    def _copy_clean(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        shutil.copytree(os.path.join(FIX, "clean", "Source"), os.path.join(tmp, "Source"))
        return tmp

    def _edit(self, tmp, rel, old, new):
        p = os.path.join(tmp, rel)
        with open(p) as f:
            text = f.read()
        self.assertIn(old, text)
        with open(p, "w") as f:
            f.write(text.replace(old, new, 1))

    def test_generated_header_with_wrong_name_caught(self):
        tmp = self._copy_clean()
        self._edit(tmp, "Source/UmbrellaElla/Public/Character/EllaCharacter.h",
                   '"EllaCharacter.generated.h"', '"UmbrellaComponent.generated.h"')
        problems = module_check.check(tmp)
        self.assertEqual([p[0] for p in problems], ["e"], problems)

    def test_minimal_api_counts_as_exported(self):
        tmp = self._copy_clean()
        self._edit(tmp, "Source/UmbrellaElla/Public/Umbrella/UmbrellaComponent.h",
                   "class UMBRELLAELLA_API UUmbrellaComponent", "class UUmbrellaComponent")
        self._edit(tmp, "Source/UmbrellaElla/Public/Umbrella/UmbrellaComponent.h",
                   "UCLASS(ClassGroup", "UCLASS(MinimalAPI, ClassGroup")
        self.assertEqual(module_check.check(tmp), [])

    def test_commented_out_include_is_ignored(self):
        tmp = self._copy_clean()
        self._edit(tmp, "Source/UmbrellaEllaEditor/Private/UmbrellaValidator.cpp",
                   '#include "Umbrella/UmbrellaComponent.h"\n',
                   '#include "Umbrella/UmbrellaComponent.h"\n// #include "UmbrellaElla/Private/Umbrella/UmbrellaRules.h"\n')
        self.assertEqual(module_check.check(tmp), [])

    def test_public_dependency_allows_public_exposure(self):
        tmp = self._copy_clean()
        # Paper2D is Public in the clean tree, which is why EllaCharacter.h may include PaperCharacter.h.
        self._edit(tmp, "Source/UmbrellaElla/UmbrellaElla.Build.cs", '"Engine", "Paper2D" }', '"Engine" }')
        self._edit(tmp, "Source/UmbrellaElla/UmbrellaElla.Build.cs", '{ "EnhancedInput"', '{ "Paper2D", "EnhancedInput"')
        self.assertEqual([p[0] for p in module_check.check(tmp)], ["c"])


class FeatureFlagRule(unittest.TestCase):
    """Rule M (GDD B section 4): gameplay code naming a gated feature checks its flag."""
    GATED = {"UMB-03": "UMB_03", "WIND-01": "WIND_01"}

    def find(self, path, code):
        return module_check.feature_flag_findings(path, code, self.GATED)

    def test_unchecked_reference_is_caught(self):
        code = "// UMB-03 sideways catch\nvoid UDefenseReceiver::TryCatch()\n{\n\tCatch();\n}\n"
        got = self.find("Source/UmbrellaElla/Private/Defense/DefenseReceiver.cpp", code)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0][0], 1)
        self.assertIn("UMB_03", got[0][1])

    def test_flag_check_passes(self):
        code = ("void UDefenseReceiver::TryCatch()\n{\n\tif (!Flags->IsFeatureEnabled(EFeatureId::UMB_03))\n\t{\n"
                "\t\treturn;\n\t}\n\tCatch(); // UMB-03\n}\n")
        self.assertEqual(self.find("Source/UmbrellaElla/Private/Defense/DefenseReceiver.cpp", code), [])

    def test_check_of_another_flag_does_not_count(self):
        code = "if (IsFeatureEnabled(EFeatureId::WIND_01)) { Catch(); } // UMB-03\n"
        got = self.find("Source/UmbrellaElla/Private/Defense/DefenseReceiver.cpp", code)
        self.assertEqual([m for _, m in got if "UMB_03" in m] != [], True)
        self.assertFalse(any("WIND_01" in m for _, m in got))

    def test_tests_flag_definitions_and_confirmed_ids_are_skipped(self):
        self.assertEqual(self.find("Source/UmbrellaElla/Private/Tests/Defense/CatchTest.cpp", "// UMB-03"), [])
        self.assertEqual(self.find("Source/UmbrellaElla/Public/Harness/FeatureFlags.h", "UMB_03,"), [])
        self.assertEqual(self.find("Source/UmbrellaElla/Private/Umbrella/Lift.cpp", "// UMB-01 lift"), [])

    def test_real_manifest_gates_every_non_confirmed_feature(self):
        gated = module_check.gated_flags(ROOT)
        self.assertEqual(len(gated), 204)              # GDD SH1.0: every Rule ID is APPROVED_P0 and flagged
        self.assertEqual(gated["OWL-16"], "OWL_16")
        self.assertEqual(gated["MOVE-13"], "MOVE_13")

    def test_tree_with_unchecked_feature_fails_through_check(self):
        d = tempfile.mkdtemp()
        try:
            shutil.copytree(os.path.join(FIX, "clean", "Source"), os.path.join(d, "Source"))
            f = os.path.join(d, "Source", "UmbrellaElla", "Private", "Umbrella", "UmbrellaComponent.cpp")
            with open(f, "a", encoding="utf-8") as fh:
                fh.write("\n// OWL-16 wing gust push\n")
            self.assertEqual([p[0] for p in module_check.check(d) if p[0] == "M"], ["M"])
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()

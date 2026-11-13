#!/usr/bin/env python3
"""Technical Director's module-boundary gate for Source/ (pipeline/unreal-rules.md,
"Modules are this project's assembly definitions" and "C++ correctness rules").

A module is any Source/**/<Name>/<Name>.Build.cs with Public/ (or Classes/) and Private/ next to it.

Rules (the tag is printed in front of each finding):
  a private-include   #include reaching into another module's Private/ (relative path or not)
  b missing-dep       a module includes a header of a module not in its Build.cs
                      PublicDependencyModuleNames / PrivateDependencyModuleNames
  c public-leak       a Public header exposes a type (include or name) of a module that is
                      only a Private dependency
  d missing-api       a UCLASS/USTRUCT in Public/ used by another module has no <MODULE>_API
                      macro (UCLASS(MinimalAPI) also counts)
  e generated-last    "X.generated.h" is not the last #include of its header, or X is not the header's name
  f raw-uobject       raw U*/A* pointer member in a UCLASS/USTRUCT body (should be TObjectPtr),
                      also inside TArray/TSet/TMap/TMultiMap/TSortedMap (TArray<AActor*>)
  g iwyu              Build.cs does not set IWYUSupport = IWYUSupport.Full

C++ standard rules (Epic coding standard + pipeline/unreal-rules.md; every .h/.cpp in a module):
  h pragma-once       a header has no "#pragma once"
  i null              NULL (use nullptr)
  j std               std:: (except std::initializer_list), #include <vector> and other STL headers,
                      try/catch/throw, dynamic_cast (use TArray/TMap, return codes, Cast<>)
  k logtemp           LogTemp (use LogUmbrellaElla)
  l using-namespace   "using namespace" anywhere; a using declaration (using X::Y;) at file scope
  m override          a header declares a known engine virtual (BeginPlay, EndPlay, Tick, TickComponent,
                      SetupPlayerInputComponent, NotifyHit, NotifyActorBeginOverlap, Falling, ... see
                      ENGINE_OVERRIDES) without override or final
  n bool-name         a bool variable, member or parameter whose name does not start with b + capital,
                      and a bitfield bool (uint8 Name : 1) whose name does not start with b + capital
  o bool-func         a header declares a bool function not starting with Is, Has, Can or Should
                      (override/final declarations are skipped; their name is the engine's)
  p braces            if / else / for / while whose body is not in { } (do-while's "while (...);" is fine)
  q switch-default    a switch with no "default:" at its top level
  r text-macro        any string literal in code not wrapped in TEXT() (OpenLevel(this, "L_Graybox"),
                      FString X = "...", asset paths, UE_LOG formats). Skipped: # lines (#include, #define
                      LOCTEXT_NAMESPACE), and literals inside the macros in TEXT_FREE_CALLS (UPROPERTY/UCLASS
                      specifiers and meta, LOCTEXT, NSLOCTEXT, static_assert, IMPLEMENT_*_MODULE,
                      IMPLEMENT_SIMPLE_AUTOMATION_TEST, UE_LOGFMT [VERIFY on 5.8.4], ...)
  s shipping-guard    TAutoConsoleVariable, FAutoConsoleCommand*, FAutoConsoleVariableRef,
                      RegisterConsoleVariable/Command or CheatManager outside "#if !UE_BUILD_SHIPPING"
                      (or the #else of "#if UE_BUILD_SHIPPING"); UFUNCTION(Exec) anywhere, because UHT
                      does not allow UFUNCTION inside such a block [VERIFY on 5.8.4]
  t indent-tabs       lines indented with spaces (Epic: tabs). One finding per file, with the count.
                      Spaces after leading tabs (alignment) are fine.
  u raw-input         IsInputKeyDown, WasInputKeyJustPressed, WasInputKeyJustReleased,
                      GetInputKeyTimeDown, GetAsyncKeyState (input goes through Enhanced Input actions)
  v looping-timer     a .cpp calls a looping SetTimer but has no ::EndPlay that calls ClearTimer or
                      ClearAllTimersForObject. Looping = the loop argument is there and is not "false"
                      (SetTimer(H, this, &F, Rate, Loop) or SetTimer(H, Delegate, Rate, Loop)), so a
                      loop flag held in a variable counts as looping

More of Epic's standard (every .h/.cpp in a module):
  w type-prefix       UCLASS deriving from an A* class starts with A, other UCLASS/UINTERFACE with U,
                      USTRUCT with F, enums with E, other classes/structs with F, T, I or S; class members,
                      member functions, locals and parameters are PascalCase (bools are rule n)
  x deferred-lambda   a lambda that captures by reference ([&], &Local), everything by copy ([=], which also
                      captures this implicitly) or raw [this] and runs later:
                      written directly inside SetTimer, SetTimerForNextTick, CreateLambda, BindLambda,
                      AddLambda, AsyncTask or Async, or stored first (auto Fn = [...]) and then passed to
                      one of them in the same function (use CreateWeakLambda(this, ...) or capture by value)
  y auto              "auto", except a lambda variable (auto Fn = [...]) and a range-based for
  z enum              a UENUM that is not "enum class EName : uint8"; any other enum (in a .h or .cpp) that is
                      not "enum class" (a plain or unnamed enum)
  A const-getter      a header member function named Get*/Is*/Has*/Can*/Should* without trailing const
                      (static, override and final are skipped)
  B const-return      a header member function returning "const T" by value
  C public-state      any data member in the public: section of a UCLASS, UPROPERTY or not; and a protected
                      data member of a UCLASS that is not tuning or an asset reference: protected is allowed
                      only for a UPROPERTY with EditDefaultsOnly, EditAnywhere or EditInstanceOnly, or a
                      member whose type is an F*Tuning struct. static and constexpr are fine, and so is a
                      UDeveloperSettings subclass (UUmbrellaTuning is read as GetDefault<UUmbrellaTuning>()->Attack.X)
  D uobject-ref       a U*/A* type passed by reference in a header (UObject& Thing); pass a pointer
  E macro-name        a #define not named UMBRELLAELLA_[A-Z0-9_]* (LOCTEXT_NAMESPACE is allowed)
  F delegate-unbind   a .cpp binds onto another object's delegate (Other->OnX.AddDynamic/AddUObject/...)
                      and no ::EndPlay (or NativeDestruct/Deinitialize/BeginDestroy) there removes OnX
  G magic-number      a number in a .cpp outside Private/Tests/ other than 0, 0.5, 1, 2, named or not:
                      const/constexpr locals and namespace-scope constants count too. Tuning goes in the
                      component's F<Comp>Tuning header; a true constant goes in a header as static constexpr
  H dead-zone         a *DeadZone* identifier (stick dead zones live in the IA_Move modifier)
  I forward-decl      a header includes a project header but uses its types only by pointer, reference,
                      TObjectPtr/TWeakObjectPtr/TSubclassOf/...; forward-declare instead
  J bool-param        a header member function of a UCLASS takes a bool by value (Move(bool bFast)): use an
                      enum or two functions. Skipped: Set<X>(bool) with one parameter, On<X> delegate
                      handlers (the delegate fixes the signature), static functions (plain rule functions
                      take state as input), override/final, and bool& / bool* out parameters
  K final             (with --rules K, or once pipeline/unreal/cpp-rules.md drops its [VERIFY] on final) a UCLASS
                      that is not final, not Abstract or Blueprintable, has no subclass in Source/ and is not
                      named in docs/asset-changes/*.json (where a Blueprint child would be listed). An actor
                      class (A prefix) inherits Blueprintable and is skipped unless it says NotBlueprintable
  L character-shell   SHELL_CLASS (AEllaCharacter) is wiring only: its .cpp may define only the constructor and
                      SetupPlayerInputComponent; the constructor never calls BindAction; and
                      SetupPlayerInputComponent calls only SHELL_INPUT_CALLS (Super, AddMappingContext,
                      ->BindInput, and the Cast/GetSubsystem lookups that reach the input subsystem)

  N determinism       gameplay code (not Private/Tests/ or Harness/) reads the wall clock (FPlatformTime::*,
                      FDateTime::Now/UtcNow) or an unseeded random (FMath::Rand*, FMath::FRand*, FMath::VRand*,
                      FMath::SRand, rand()): draws come from the seeded FRandomStream so one seed replays one
                      run (GDD QA-08)
  O mutable-static    a static variable that is not const or constexpr (static locals, static members,
                      namespace-scope statics, static delegates): PIE keeps the module loaded, so the value
                      leaks into the next run. Static functions and console variables (rule s) are skipped
  P container-getter  a header function returns a non-const reference or pointer to a TArray/TMap/TSet/...
                      (TArray<FBolt>& GetBolts()): return const& or a copy so only the owner writes it

Feature switches (GDD B section 4; pipeline/unreal-rules.md, "Feature flags"):
  M feature-flag      a gameplay file (not Private/Tests/, not a *FeatureFlags* file) names a gated feature ID (a
                      docs/feature-manifest.json record with a flag: UMB-02 or UMB_02, in code or comments) but never
                      calls IsFeatureEnabled(...<FLAG>...) for it. The manifest is read from --root, else this repo

Limits (regex, not a compiler):
  - Engine headers are mapped to modules only through ENGINE_HEADERS below. Other engine includes
    are trusted, so rule b/c only covers project modules plus that table.
  - Rule f looks at member declarations at the top brace level of a reflected class/struct body.
    It skips function declarations (anything with "(") and F*/I*/T* types. A non-UObject class
    named with a U or A prefix would be a false positive; a pointer hidden behind a typedef or
    macro is a false negative.
  - Rule c/d match type names by word. A same-named local identifier would count as a use.
  - #if/#ifdef blocks are not evaluated; every include counts. Only rule s reads #if lines.
  - Rules h-v see code with comments and string contents blanked, except rule r, which reads literals.
  - Rule m only knows the names in ENGINE_OVERRIDES. Other overrides are left to the reviewer.
    ReceiveHit is a BlueprintImplementableEvent with no C++ virtual, so it is not in the list.
  - Rule n misses bools declared through a typedef or macro. Bitfields are checked only as uint8/uint32 X : 1.
  - Rule v reads the loop argument by position; a timer cleared in another file is not seen. Delegate
    unbinding in EndPlay is left to rule F.
  - Rule r does not parse raw string literals R"(...)". A macro that needs a plain char literal and is not in
    TEXT_FREE_CALLS is a false positive: add it to the list with a test.
  - Rules w, A, B, C read class bodies at their top level only; a member declared through a macro is missed.
  - Rule x follows a stored lambda only by its variable name inside the same outermost { } block. A lambda
    passed through a helper function or a member variable is missed.
  - Rule w reads locals and parameters as "<Type> <name>" with a capitalised or built-in type; a lowercase
    type (a typedef) hides the name.
  - Rule y allows auto in every range-based for (a regex cannot tell a map from an array).
  - Rule D checks headers only; a .cpp-only function is missed.
  - Rule F skips own subobjects (X = CreateDefaultSubobject in the same .cpp, GetCapsuleComponent() and the
    like). A widget binding its own BindWidget button needs RemoveAll in NativeDestruct or is a false positive.
  - Rule I only follows project headers; an engine header that could be forward-declared is not seen.
  - Rule K is off while UHT support for final on a UCLASS is [VERIFY] in pipeline/unreal/cpp-rules.md (k_proven),
    unless asked for (--rules K). It turns on by itself when card 0.4a pastes the card 0.3 compile log of a final
    UCLASS there and removes that [VERIFY]: the measurement, not a gate patch, switches it.
  - Rule L knows the shell only by its class name, and reads calls by name ("Cast", "BindInput").
  - Rule C cannot tell tuning from state by meaning; it trusts the Edit* specifier and the F*Tuning name.
  - Rule J cannot tell a bool that picks a behavior from one that passes state; it flags every by-value bool
    outside the skipped forms.
  - Rule N reads names only; a clock or random reached through a helper or another module is missed, and
    TMap/TSet iteration order (also not repeatable) is left to the reviewer.
  - Rule O treats a static declaration whose first bracket is "(" as a function, so a static variable
    initialised with parentheses (static int32 X(0);) is missed.

Usage: python3 tools/module_check.py [--root PATH] [--rules LETTERS]   (e.g. --rules hijk; letters are case-sensitive;
       rule K runs when K is in --rules or once cpp-rules.md proves final on a UCLASS)
Exit 0 = clean, 1 = problems, 2 = no Source/ folder (nothing to check; CI treats it as a skip).
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Engine header -> module, for the dependencies this game is likely to forget.
# Key is a regex on the include path. Keep it to unambiguous headers.
ENGINE_HEADERS = [
    (r"^Paper\w*\.h$|^PaperCharacter\.h$", "Paper2D"),
    (r"^EnhancedInput\w*\.h$|^InputAction\.h$|^InputMappingContext\.h$|^InputActionValue\.h$", "EnhancedInput"),
    (r"^Engine/DeveloperSettings\.h$", "DeveloperSettings"),
    (r"^Blueprint/UserWidget\.h$|^Components/(TextBlock|Image|ProgressBar|Button|CanvasPanel)\.h$", "UMG"),
    (r"^EditorValidatorBase\.h$", "DataValidation"),
]

INCLUDE_RE = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', re.M)
DECL_RE = re.compile(r"\b(UCLASS|USTRUCT)\s*\(((?:[^()]|\([^()]*\))*)\)\s*(?:class|struct)\s+((?:\w+_API\s+)?)(\w+)")
TYPE_DECL_RE = re.compile(r"^\s*(?:class|struct)\s+(?:\w+_API\s+)?([UAF][A-Z]\w*)\b(?!\s*;)", re.M)
RAW_PTR_RE = re.compile(r"^\s*(?:(?:const|mutable|static)\s+)*(?:class\s+)?([UA][A-Z]\w*)\s*\*\s*(?:const\s+)?\w+\s*(?:=[^;(]*)?;")
CONTAINER_PTR_RE = re.compile(r"^\s*(?:(?:const|mutable|static)\s+)*(TArray|TSet|TMap|TMultiMap|TSortedMap)\s*<(.*)>\s*\w+\s*(?:=[^;(]*)?;", re.S)
INNER_PTR_RE = re.compile(r"(?<![\w<])(?:class\s+)?([UA][A-Z]\w*)\s*\*")
HEADER_EXT = (".h", ".hpp", ".inl")
CODE_EXT = HEADER_EXT + (".cpp", ".cc")


CHAR_LIT_RE = re.compile(r"'(?:\\.|[^'\\\n])'")


def string_end(text, i):
    """Index just past the string literal that starts at text[i] == '"' (stops at a newline)."""
    j, n = i + 1, len(text)
    while j < n and text[j] not in '"\n':
        j += 2 if text[j] == "\\" else 1
    return min(j + 1, n) if j < n and text[j] == '"' else j


def blank_strings(text):
    """Blank the contents of string and char literals (quotes kept, length kept)."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = string_end(text, i)
            closed = j - i >= 2 and text[j - 1] == '"'
            out.append('"' + " " * (j - i - 1 - closed) + '"' * closed)
            i = j
        elif c == "'" and CHAR_LIT_RE.match(text, i):
            j = CHAR_LIT_RE.match(text, i).end()
            out.append("'" + " " * (j - i - 2) + "'")
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def strip_comments(text):
    """Blank out comments (keeping newlines, strings and include paths) so
    line numbers stay right and commented-out code is ignored."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = string_end(text, i)
            out.append(text[i:j])
            i = j
        elif c == "'" and CHAR_LIT_RE.match(text, i):
            j = CHAR_LIT_RE.match(text, i).end()
            out.append(text[i:j])
            i = j
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(ch if ch == "\n" else " " for ch in text[i:j]))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def parse_build_cs(text):
    text = strip_comments(text)
    deps = {}
    for kind in ("Public", "Private"):
        names = set()
        for m in re.finditer(kind + r"DependencyModuleNames\s*\.\s*(?:AddRange|Add)\s*\((.*?)\)\s*;", text, re.S):
            names.update(re.findall(r'"([^"]+)"', m.group(1)))
        for m in re.finditer(kind + r"DependencyModuleNames\s*=\s*new[^{;]*\{(.*?)\}", text, re.S):
            names.update(re.findall(r'"([^"]+)"', m.group(1)))
        deps[kind] = names
    iwyu = re.search(r"\bIWYUSupport\s*=\s*IWYUSupport\.Full\b", text) is not None
    return deps["Public"], deps["Private"], iwyu


class Module:
    def __init__(self, name, path, build_cs):
        self.name = name
        self.path = path
        self.build_cs = build_cs
        with open(build_cs, encoding="utf-8", errors="replace") as f:
            self.public_deps, self.private_deps, self.iwyu = parse_build_cs(f.read())
        self.files = []
        for d, _, fs in os.walk(path):
            for f in fs:
                if f.endswith(CODE_EXT):
                    self.files.append(os.path.join(d, f))
        self.public_dirs = [os.path.join(path, p) for p in ("Public", "Classes")]
        self.private_dir = os.path.join(path, "Private")

    @property
    def deps(self):
        return self.public_deps | self.private_deps

    def area(self, f):
        if any(within(f, d) for d in self.public_dirs):
            return "Public"
        if within(f, self.private_dir):
            return "Private"
        return "Other"


def within(path, folder):
    path, folder = os.path.normpath(path), os.path.normpath(folder)
    return path == folder or path.startswith(folder + os.sep)


def find_modules(source):
    mods = []
    for d, _, fs in os.walk(source):
        for f in fs:
            if f.endswith(".Build.cs"):
                name = f[: -len(".Build.cs")]
                mods.append(Module(name, d, os.path.join(d, f)))
    return mods


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def final_findings(root, mods):
    """Rule K: a UCLASS nothing derives from (no subclass in Source/, no Blueprint child in
    docs/asset-changes/*.json) is final. [VERIFY UHT accepts final on a UCLASS on 5.8.4]"""
    classes, bases = [], set()
    for m in mods:
        for f in m.files:
            code = blank_strings(strip_comments(read(f)))
            for kind, name, base, macro, npos, open_, close in type_defs(code):
                bases.update(re.findall(r"\b[A-Z]\w*", base))
                if macro != "UCLASS":
                    continue
                spec = REFLECT_MACRO_RE.search(code[max(0, npos - 600):npos].rsplit("class", 1)[0].rstrip() + "\n")
                spec_text = spec.group(2) if spec else ""
                head = code[npos:open_]
                classes.append((f, line_of(code, npos), name, spec_text, re.search(r"\bfinal\b", head)))
    sidecars = ""
    side_dir = os.path.join(root, "docs", "asset-changes")
    if os.path.isdir(side_dir):
        for fn in sorted(os.listdir(side_dir)):
            if fn.endswith(".json"):
                sidecars += read(os.path.join(side_dir, fn)) + "\n"
    out = []
    for f, ln, name, spec, is_final in classes:
        if is_final or name in bases or re.search(r"\b(Abstract|Blueprintable)\b", spec, re.I):
            continue
        # final-9 A M8: an A-class (an Actor: AGameModeBase, ACharacter, ...) inherits Blueprintable, and the docs
        # give the GameMode and the Ella shell Blueprint children (card 0.8: BP_GameMode, BP_Ella) in a later card
        # whose lane has no docs/asset-changes/. Only an explicit NotBlueprintable actor must be final.
        if name.startswith("A") and not re.search(r"\bNotBlueprintable\b", spec, re.I):
            continue
        if re.search(r"\b(?:" + name + "|" + name[1:] + r")\b", sidecars):
            continue
        out.append((f, ln, f"UCLASS {name} has no subclass in Source/ and no Blueprint child in docs/asset-changes/; "
                           f"mark it final"))
    return out


FINAL_VERIFY = re.compile(r"`final`[^\n]*\[VERIFY UHT accepts it on a UCLASS")


def k_proven(root):
    """True once pipeline/unreal/cpp-rules.md no longer marks `final` on a UCLASS as [VERIFY] (card 0.4a removes the
    tag when it pastes card 0.3's compile log of one). A missing file is not proof."""
    try:
        with open(os.path.join(root, "pipeline", "unreal", "cpp-rules.md"), encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return False
    return "`final`" in text and not FINAL_VERIFY.search(text)


def check(root, with_k=None):
    """with_k None: rule K runs once k_proven(root)."""
    if with_k is None:
        with_k = k_proven(root)
    source = os.path.join(root, "Source")
    if not os.path.isdir(source):
        return None
    mods = find_modules(source)
    by_name = {m.name: m for m in mods}
    problems = []
    seen_d = set()

    def rel(p):
        return os.path.relpath(p, root).replace(os.sep, "/")

    def add(rule, path, line, msg):
        problems.append((rule, f"{rel(path)}:{line}" if line else rel(path), msg))

    def owner(path):
        best = None
        for m in mods:
            if within(path, m.path) and (best is None or len(m.path) > len(best.path)):
                best = m
        return best

    # Public header index: include path (relative to Public/ or Classes/) -> module.
    public_index, private_index = {}, {}
    types = {}  # type name -> (module, header, has_api, line)
    for m in mods:
        for f in m.files:
            area = m.area(f)
            if area == "Public":
                for d in m.public_dirs:
                    if within(f, d):
                        public_index.setdefault(os.path.relpath(f, d).replace(os.sep, "/"), m)
                text = strip_comments(read(f))
                for dm in DECL_RE.finditer(text):
                    spec, api, name = dm.group(2), dm.group(3).strip(), dm.group(4)
                    has_api = api == m.name.upper() + "_API" or "MinimalAPI" in spec
                    types[name] = (m, f, has_api, line_of(text, dm.start()))
                for tm in TYPE_DECL_RE.finditer(text):
                    types.setdefault(tm.group(1), (m, f, True, line_of(text, tm.start())))
            elif area == "Private":
                private_index.setdefault(os.path.relpath(f, m.private_dir).replace(os.sep, "/"), m)

    # Project header -> type names it defines (rule I), and include path -> header file.
    header_types, header_paths = {}, {}
    for m in mods:
        for f in m.files:
            if not f.endswith(HEADER_EXT):
                continue
            code = blank_strings(strip_comments(read(f)))
            header_types[f] = [d[1] for d in type_defs(code)] + [e.group(2) for e in ENUM_RE.finditer(code)]
            for d in m.public_dirs + [m.private_dir]:
                if within(f, d):
                    header_paths.setdefault(os.path.relpath(f, d).replace(os.sep, "/"), f)

    def header_file(f, inc):
        cand = os.path.normpath(os.path.join(os.path.dirname(f), inc))
        if cand in header_types:
            return cand
        return header_paths.get(inc)

    def resolve(f, inc):
        """Return (module_name, area, how) for an include, or (None, None, None) if unknown/engine-unmapped."""
        # 1. relative to the including file (how "../" includes resolve)
        cand = os.path.normpath(os.path.join(os.path.dirname(f), inc))
        if os.path.isfile(cand):
            om = owner(cand)
            if om:
                return om.name, om.area(cand), "relative"
        # 2. an explicit "<Module>/Private/..." or "<Module>/Public/..." path
        parts = inc.replace("\\", "/").split("/")
        for i, p in enumerate(parts[:-1]):
            if p in ("Private", "Public", "Classes") and i > 0 and parts[i - 1] in by_name:
                return parts[i - 1], "Private" if p == "Private" else "Public", "module path"
        # 3. the normal include path: another module's Public/
        if inc in public_index:
            return public_index[inc].name, "Public", "include path"
        if inc in private_index:
            return private_index[inc].name, "Private", "include path"
        for pat, mod in ENGINE_HEADERS:
            if re.search(pat, inc):
                return mod, "Public", "engine"
        return None, None, None

    for m in mods:
        if not m.iwyu:
            add("g", m.build_cs, 0, "IWYUSupport is not set to IWYUSupport.Full")
        for f in m.files:
            raw = read(f)
            text = strip_comments(raw)
            area = m.area(f)
            incs = [(mm.group(1), line_of(text, mm.start())) for mm in INCLUDE_RE.finditer(text)]
            for inc, ln in incs:
                target, tarea, how = resolve(f, inc)
                if target is None:
                    if "/Private/" in "/" + inc.replace("\\", "/") and target != m.name:
                        own = os.path.normpath(os.path.join(os.path.dirname(f), inc))
                        if not within(own, m.path):
                            add("a", f, ln, f'"{inc}" reaches into a Private/ folder outside {m.name}')
                    continue
                if target == m.name:
                    if area == "Public" and tarea == "Private":
                        add("c", f, ln, f'Public header includes its own Private header "{inc}"')
                    continue
                if tarea == "Private":
                    add("a", f, ln, f'"{inc}" reaches into {target}/Private/ ({how}); include its Public header instead')
                    continue
                if target not in m.deps:
                    add("b", f, ln, f'includes "{inc}" from module {target}, which is not in {m.name}.Build.cs dependencies')
                elif area == "Public" and target not in m.public_deps:
                    add("c", f, ln, f'Public header includes "{inc}" from {target}, which is only a Private dependency; '
                                    f'move the include to the .cpp or make {target} Public')
            # rule e: generated.h last, and named after this header
            if f.endswith(HEADER_EXT):
                gen = [(i, inc, ln) for i, (inc, ln) in enumerate(incs) if inc.endswith(".generated.h")]
                for i, inc, ln in gen:
                    if i != len(incs) - 1:
                        add("e", f, ln, f'"{inc}" must be the last #include (found "{incs[-1][0]}" after it)')
                    stem = os.path.splitext(os.path.basename(f))[0]
                    if os.path.basename(inc) != stem + ".generated.h":
                        add("e", f, ln, f'"{inc}" does not match this header; expected "{stem}.generated.h"')
            # rule c (by type name) and rule d
            for tname, (tm, thdr, has_api, tline) in types.items():
                if tm is m or not re.search(r"\b" + tname + r"\b", text):
                    continue
                if area == "Public" and tm.name in m.deps and tm.name not in m.public_deps:
                    mm = re.search(r"\b" + tname + r"\b", text)
                    add("c", f, line_of(text, mm.start()), f"Public header exposes {tname} from {tm.name}, which is only a Private dependency")
                if not has_api:
                    key = ("d", thdr, tname)
                    if key not in seen_d:
                        seen_d.add(key)
                        add("d", thdr, tline, f"{tname} is used by {m.name} but has no {tm.name.upper()}_API (or MinimalAPI)")
            # rule f
            for _, ln, msg in raw_uobject_members(text):
                add("f", f, ln, msg)
            # rules h-v, w-z, A-H
            for rule, ln, msg in style_findings(f, raw) + standard_findings(f, raw):
                add(rule, f, ln, msg)
            # rule I
            if f.endswith(HEADER_EXT):
                proj = []
                for inc, ln in incs:
                    target = header_file(f, inc)
                    if target and target != f and not inc.endswith(".generated.h"):
                        proj.append((inc, ln, target))
                for ln, msg in forward_decl_findings(f, blank_strings(text), proj, header_types):
                    add("I", f, ln, msg)
    gated = gated_flags(root)
    for m in mods:
        for f in m.files:
            for ln, msg in feature_flag_findings(f, read(f), gated):
                add("M", f, ln, msg)
    if with_k:
        for f, ln, msg in final_findings(root, mods):
            add("K", f, ln, msg)
    problems.sort(key=lambda p: (p[1], p[0]))
    return problems



def gated_flags(root):
    """{feature id: flag} for every manifest record with a flag (every non-CONFIRMED feature)."""
    import json
    for base in (root, ROOT):
        path = os.path.join(base, "docs", "feature-manifest.json")
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
            except (OSError, ValueError):
                return {}
            return {r["feature_id"]: r["flag"] for r in data.get("features", []) if r.get("flag")}
    return {}


def feature_flag_findings(path, raw, gated):
    """Rule M: a gameplay file that names a gated feature must check its flag (IsFeatureEnabled(...FLAG...))."""
    p = path.replace(os.sep, "/")
    if "/Private/Tests/" in p or "FeatureFlag" in os.path.basename(p) or not gated:
        return []
    checked = {m.group(1) for m in re.finditer(r"\bIsFeatureEnabled\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)", raw)}
    checked_text = " ".join(checked)
    out = []
    # A `// bake: UMB-01.ascent_speed` marker names the key the bake writes, not gated behavior (final-8 honest path:
    # every F<Comp>Tuning header carries markers, pipeline/unreal-rules.md)
    named = re.sub(r"//\s*bake:\s*\S+", "", raw)
    for fid, flag in sorted(gated.items()):
        m = re.search(r"(?<![\w-])(?:" + re.escape(fid) + "|" + re.escape(flag) + r")(?![\w-])", named)
        if m and not re.search(r"\b" + re.escape(flag) + r"\b", checked_text):
            out.append((line_of(raw, m.start()), f"names gated feature {fid} but never calls IsFeatureEnabled(...{flag}...);"
                                                 f" build it behind its flag (default from docs/feature-manifest.json)"))
    return out


def raw_uobject_members(text):
    """Yield (pos, line, message) for raw UObject pointer members at the top level of UCLASS/USTRUCT bodies."""
    out = []
    for dm in DECL_RE.finditer(text):
        start = text.find("{", dm.end())
        semi = text.find(";", dm.end())
        if start < 0 or (0 <= semi < start):
            continue
        depth, i, line_start = 0, start, start + 1
        body_end = len(text)
        while i < len(text):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    body_end = i
                    break
            i += 1
        # walk statements at depth 1
        depth, buf, buf_start = 0, [], start + 1
        for j in range(start + 1, body_end):
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                buf, buf_start = [], j + 1
                continue
            if depth:
                continue
            if ch == ";":
                stmt = "".join(buf)
                stmt_l = re.sub(r"\b(UPROPERTY|GENERATED_BODY|GENERATED_UCLASS_BODY|UFUNCTION)\s*\((?:[^()]|\([^()]*\))*\)", " ", stmt)
                stmt_l = re.sub(r"\b(public|private|protected)\s*:", " ", stmt_l)
                m = RAW_PTR_RE.match(stmt_l.strip() + ";") if "(" not in stmt_l else None
                cm = CONTAINER_PTR_RE.match(stmt_l.strip() + ";") if "(" not in stmt_l and not m else None
                inner = INNER_PTR_RE.search(cm.group(2)) if cm else None
                if inner:
                    decl = re.search(r"\b" + cm.group(1) + r"\s*<", stmt)
                    off = buf_start + (decl.start() if decl else 0)
                    out.append((off, line_of(text, off), f"raw pointer '{inner.group(1)}*' inside {cm.group(1)} member "
                                f"'{stmt_l.strip()};' in reflected body; use TObjectPtr<{inner.group(1)}>"))
                if m:
                    decl = re.search(r"\b" + m.group(1) + r"\s*\*", stmt)
                    off = buf_start + (decl.start() if decl else 0)
                    out.append((off, line_of(text, off), f"raw pointer member '{stmt_l.strip()};' in reflected body; use TObjectPtr<{m.group(1)}> (or TWeakObjectPtr if non-owning)"))
                buf, buf_start = [], j + 1
            else:
                buf.append(ch)
    return out


# ---------------------------------------------------------------- rules h-v (C++ standard)

ENGINE_OVERRIDES = (
    "BeginPlay", "EndPlay", "Tick", "TickComponent", "SetupPlayerInputComponent", "PostInitializeComponents",
    "BeginDestroy", "OnRegister", "OnUnregister", "InitializeComponent", "UninitializeComponent", "PostLoad",
    "OnConstruction", "Destroyed", "PossessedBy", "UnPossessed", "Landed", "NativeConstruct", "NativeDestruct",
    "NativeTick", "NativeOnInitialized", "StartupModule", "ShutdownModule", "GetLifetimeReplicatedProps",
    "CanValidateAsset_Implementation", "ValidateLoadedAsset_Implementation",
    # 2D gameplay hit, overlap and movement virtuals (AActor, ACharacter) [VERIFY names in 5.8.4 Actor.h, Character.h]
    "NotifyHit", "NotifyActorBeginOverlap", "NotifyActorEndOverlap", "OnJumped_Implementation", "Falling",
    "OnMovementModeChanged", "NotifyJumpApex", "OnWalkingOffLedge_Implementation", "PostEditChangeProperty",
)
STL_HEADERS = ("vector", "map", "set", "list", "deque", "array", "string", "string_view", "unordered_map",
               "unordered_set", "algorithm", "memory", "functional", "iostream", "sstream", "fstream", "thread",
               "mutex", "chrono", "utility", "optional", "variant", "tuple", "regex", "random", "exception",
               "stdexcept", "typeinfo")
BOOL_PREFIXES = ("Is", "Has", "Can", "Should")
# Macros whose string arguments are not code: reflection specifiers, localization macros (they add TEXT()
# themselves), and macros that need a plain char literal. A literal inside one of these is not rule r.
TEXT_FREE_CALLS = ("UPROPERTY", "UFUNCTION", "UCLASS", "USTRUCT", "UENUM", "UINTERFACE", "UMETA", "UPARAM",
                   "UDELEGATE", "TEXT", "LOCTEXT", "NSLOCTEXT", "INVTEXT", "LOCTABLE", "TEXTVIEW", "UTF8TEXT",
                   "WIDETEXT", "static_assert", "UE_DEPRECATED", "IMPLEMENT_PRIMARY_GAME_MODULE",
                   "IMPLEMENT_GAME_MODULE", "IMPLEMENT_MODULE", "IMPLEMENT_SIMPLE_AUTOMATION_TEST",
                   "IMPLEMENT_COMPLEX_AUTOMATION_TEST", "IMPLEMENT_CUSTOM_SIMPLE_AUTOMATION_TEST",
                   "BEGIN_DEFINE_SPEC", "DEFINE_SPEC", "UE_LOGFMT")
CONSOLE_RE = re.compile(r"\b(TAutoConsoleVariable|FAutoConsoleCommand\w*|FAutoConsoleVariableRef|RegisterConsoleVariable"
                        r"|RegisterConsoleCommand|U?CheatManager\w*)\b")
EXEC_RE = re.compile(r"\bUFUNCTION\s*\(([^()]|\([^()]*\))*\bExec\b")
RAW_INPUT_RE = re.compile(r"\b(IsInputKeyDown|WasInputKeyJustPressed|WasInputKeyJustReleased|GetInputKeyTimeDown"
                          r"|GetAsyncKeyState)\s*\(")
BOOL_VAR_RE = re.compile(r"\bbool\s*&?\s+&?\s*(?:const\s+)?(?!b[A-Z0-9])([A-Za-z_]\w*)\s*(?=[,;)=\[{]|:(?!:))")
BITFIELD_BOOL_RE = re.compile(r"\buint(?:8|32)\s+(?!b[A-Z0-9])([A-Za-z_]\w*)\s*:\s*1\s*(?=[;=,{])")


def match_close(text, i):
    """text[i] is ( [ or {; return the index of its match, or -1."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack = []
    for j in range(i, len(text)):
        ch = text[j]
        if ch in pairs:
            stack.append(pairs[ch])
        elif stack and ch == stack[-1]:
            stack.pop()
            if not stack:
                return j
    return -1


def enclosing_calls(code, pos):
    """Names of the calls whose argument lists contain pos, innermost first (None where no name is seen).
    Stops at the start of the statement (a ; or an unmatched { at the same level)."""
    names, depth = [], 0
    for k in range(pos - 1, -1, -1):
        ch = code[k]
        if ch in ")]}":
            depth += 1
        elif ch in "([{":
            if depth:
                depth -= 1
                continue
            if ch == "{":
                break
            if ch == "(":
                m = re.search(r"(\w+)\s*(?:<[^<>;]*(?:<[^<>;]*>)?[^<>;]*>)?\s*$", code[max(0, k - 200):k])   # bounded: the unbounded search backtracked for minutes on long files
                names.append(m.group(1) if m else None)
        elif ch == ";" and depth == 0:
            break
    return names


def skip_ws(text, i):
    while i < len(text) and text[i].isspace():
        i += 1
    return i


def top_level_args(text):
    """Split a call's argument text at commas that are not nested."""
    args, depth, cur = [], 0, []
    for ch in text:
        if ch in "([{<":
            depth += 1
        elif ch in ")]}>":
            depth -= 1
        if ch == "," and depth == 0:
            args.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    args.append("".join(cur))
    return [a.strip() for a in args]


def shipping_guarded_lines(code):
    """Set of line numbers that sit inside #if !UE_BUILD_SHIPPING (or the #else of #if UE_BUILD_SHIPPING)."""
    neg = re.compile(r"!\s*\(?\s*UE_BUILD_SHIPPING\b|\bUE_BUILD_SHIPPING\s*==\s*0\b")
    pos = re.compile(r"^\s*\(?\s*UE_BUILD_SHIPPING\s*(?:==\s*1\s*)?\)?\s*$")
    stack, guarded = [], set()
    for n, line in enumerate(code.split("\n"), 1):
        m = re.match(r"\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)", line)
        if m:
            kind, cond = m.group(1), m.group(2)
            if kind in ("if", "ifdef", "ifndef"):
                is_if = kind == "if"
                stack.append([is_if and bool(neg.search(cond)), is_if and bool(pos.match(cond))])
            elif kind == "elif" and stack:
                stack[-1] = [bool(neg.search(cond)), False]
            elif kind == "else" and stack:
                stack[-1] = [stack[-1][1], False]
            elif kind == "endif" and stack:
                stack.pop()
            continue
        if any(s[0] for s in stack):
            guarded.add(n)
    return guarded


def timer_loops(args):
    """True when a SetTimer call loops: its loop argument is present and is not false.
    SetTimer(Handle, Object, &Method, Rate, Loop, ...) or SetTimer(Handle, Delegate/Lambda, Rate, Loop, ...)."""
    obj_form = len(args) > 2 and (args[1] == "this" or args[2].startswith("&"))
    idx = 4 if obj_form else 3
    return len(args) > idx and args[idx] not in ("false", "")


def style_findings(path, raw):
    """Rules h-v for one source file. Returns [(rule, line, message)]."""
    nocom = strip_comments(raw)
    code = blank_strings(nocom)
    is_header = path.endswith(HEADER_EXT)
    out = []

    def at(rule, pos, msg):
        out.append((rule, line_of(code, pos), msg))

    # h
    if is_header and not re.search(r"^\s*#\s*pragma\s+once\b", code, re.M):
        out.append(("h", 1, 'header has no "#pragma once"'))
    # i
    for m in re.finditer(r"\bNULL\b", code):
        at("i", m.start(), "NULL; use nullptr")
    # j
    for m in re.finditer(r"\bstd\s*::\s*(?!initializer_list\b)(\w+)", code):
        at("j", m.start(), f"std::{m.group(1)}; use the UE type (TArray, TMap, FString, MoveTemp, ...)")
    for m in re.finditer(r"^\s*#\s*include\s*<(\w+)>", code, re.M):
        if m.group(1) in STL_HEADERS:
            at("j", m.start(1), f"#include <{m.group(1)}>: no standard library containers or algorithms")
    for m in re.finditer(r"\bdynamic_cast\s*<", code):
        at("j", m.start(), "dynamic_cast; use Cast<> or CastChecked<>")
    for m in re.finditer(r"\b(?:try\s*\{|catch\s*\(|throw\b)", code):
        at("j", m.start(), "C++ exceptions are off in UE modules; use return codes")
    # k
    for m in re.finditer(r"\bLogTemp\b", code):
        at("k", m.start(), "LogTemp; use LogUmbrellaElla")
    # l
    for m in re.finditer(r"^\s*using\s+namespace\b", code, re.M):
        at("l", m.start(), '"using namespace"; name the namespace where it is used')
    for m in re.finditer(r"^\s*using\s+(?!namespace\b)[\w:]*::\w+\s*;", code, re.M):
        if code.count("{", 0, m.start()) == code.count("}", 0, m.start()):
            at("l", m.start(), "using declaration at file scope; put it inside the function or namespace that needs it")
    # m
    if is_header:
        for m in re.finditer(r"(?<!::)\b(" + "|".join(ENGINE_OVERRIDES) + r")\s*\(", code):
            close = match_close(code, m.end() - 1)
            if close < 0 or re.search(r"[.>]\s*$", code[:m.start()]):
                continue
            tail = re.match(r"[^;{]*", code[close + 1:]).group(0)
            if not re.search(r"\b(override|final)\b", tail):
                at("m", m.start(), f"{m.group(1)} overrides an engine virtual; add override")
    # n
    for m in BOOL_VAR_RE.finditer(code):
        if m.group(1) != "operator":
            at("n", m.start(1), f"bool '{m.group(1)}' must start with b (b{m.group(1)[:1].upper()}{m.group(1)[1:]})")
    for m in BITFIELD_BOOL_RE.finditer(code):
        at("n", m.start(1), f"bitfield bool '{m.group(1)} : 1' must start with b (b{m.group(1)[:1].upper()}{m.group(1)[1:]})")
    # o
    if is_header:
        for m in re.finditer(r"(?<!::)\bbool\s+([A-Z]\w*)\s*\(", code):
            name = m.group(1)
            close = match_close(code, m.end() - 1)
            tail = re.match(r"[^;{]*", code[close + 1:]).group(0) if close >= 0 else ""
            if re.search(r"\b(override|final)\b", tail) or name.startswith(BOOL_PREFIXES):
                continue
            at("o", m.start(1), f"bool function '{name}' should ask a question: start it with {', '.join(BOOL_PREFIXES)}")
    # p
    for m in re.finditer(r"\b(if|for|while)\s*\(", code):
        ls = code.rfind("\n", 0, m.start()) + 1
        if code[ls:m.start()].strip().startswith("#"):
            continue
        close = match_close(code, m.end() - 1)
        if close < 0:
            continue
        j = skip_ws(code, close + 1)
        nxt = code[j:j + 1]
        if nxt == "{" or (m.group(1) == "while" and nxt == ";"):
            continue
        at("p", m.start(), f"'{m.group(1)}' body must be in braces")
    for m in re.finditer(r"\belse\b", code):
        ls = code.rfind("\n", 0, m.start()) + 1
        if code[ls:m.start()].strip().startswith("#"):
            continue
        j = skip_ws(code, m.end())
        if code[j:j + 1] != "{" and not re.match(r"if\b", code[j:]):
            at("p", m.start(), "'else' body must be in braces")
    # q
    for m in re.finditer(r"\bswitch\s*\(", code):
        close = match_close(code, m.end() - 1)
        j = skip_ws(code, close + 1) if close >= 0 else -1
        if j < 0 or code[j:j + 1] != "{":
            continue
        end = match_close(code, j)
        body, depth = [], 0
        for ch in code[j + 1:end if end > 0 else len(code)]:
            if ch in "{(":
                depth += 1
            elif ch in "})":
                depth -= 1
            elif depth == 0:
                body.append(ch)
        if not re.search(r"\bdefault\s*:", "".join(body)):
            at("q", m.start(), "switch has no default case")
    # r: every string literal in code is inside TEXT() (or a macro that takes plain literals)
    for lm in re.finditer(r'"[^"\n]*"', code):
        ls = code.rfind("\n", 0, lm.start()) + 1
        if code[ls:lm.start()].lstrip().startswith("#") or re.search(r"\b(extern|operator)\s*$", code[ls:lm.start()]):
            continue
        calls = enclosing_calls(code, lm.start())
        if any(c in TEXT_FREE_CALLS for c in calls):
            continue
        lit = nocom[lm.start():lm.end()]
        where = f" in {calls[0]}()" if calls and calls[0] else ""
        at("r", lm.start(), f"string literal {lit}{where}; wrap it in TEXT()")
    # s
    guarded = shipping_guarded_lines(code)
    for m in CONSOLE_RE.finditer(code):
        if line_of(code, m.start()) not in guarded:
            at("s", m.start(), f"{m.group(1)} outside #if !UE_BUILD_SHIPPING")
    for m in EXEC_RE.finditer(code):
        at("s", m.start(), "UFUNCTION(Exec) cannot be compiled out of Shipping; use the dev-only ue.Debug cvar")
    # t
    spaced = [m.start() for m in re.finditer(r"^ +\S", code, re.M)]
    if spaced:
        at("t", spaced[0], f"{len(spaced)} line(s) indented with spaces; indent with tabs")
    # u
    for m in RAW_INPUT_RE.finditer(code):
        at("u", m.start(), f"{m.group(1)} is raw key polling; bind an Enhanced Input action in BindInput")
    # v
    if not is_header:
        loops = []
        for m in re.finditer(r"\bSetTimer\s*\(", code):
            close = match_close(code, m.end() - 1)
            if close >= 0 and timer_loops(top_level_args(code[m.end():close])):
                loops.append(m.start())
        if loops:
            cleared = False
            for em in re.finditer(r"::\s*EndPlay\s*\(", code):
                close = match_close(code, em.end() - 1)
                j = skip_ws(code, close + 1) if close >= 0 else -1
                if j >= 0 and code[j:j + 1] == "{":
                    body = code[j:match_close(code, j) + 1]
                    if re.search(r"\b(ClearTimer|ClearAllTimersForObject)\s*\(", body):
                        cleared = True
            if not cleared:
                for pos in loops:
                    at("v", pos, "looping timer, but no ::EndPlay here clears it (ClearTimer on its saved FTimerHandle)")
    return out


# ---------------------------------------------------------------- rules w-z, A-I (more of Epic's standard)

DEFERRED_CALLS = ("SetTimer", "SetTimerForNextTick", "CreateLambda", "BindLambda", "AddLambda", "AsyncTask", "Async")
# Project #define names. LOCTEXT_NAMESPACE is Epic's required localization define.
MACRO_PREFIXES = ("UMBRELLAELLA_",)
MACRO_ALLOWED = ("LOCTEXT_NAMESPACE",)
# Literals a .cpp may use without a name. Everything else is a tuning value or a named constant.
ALLOWED_NUMBERS = (0.0, 0.5, 1.0, 2.0)
GETTER_PREFIXES = ("Get", "Is", "Has", "Can", "Should")
PTR_WRAPPERS = ("TObjectPtr", "TWeakObjectPtr", "TSoftObjectPtr", "TSubclassOf", "TSoftClassPtr", "TLazyObjectPtr")
DELEGATE_ADD = ("AddDynamic", "AddUniqueDynamic", "AddUObject", "AddLambda", "AddWeakLambda", "AddUFunction", "AddRaw", "AddSP")
OWN_COMPONENT_GETTERS = re.compile(r"^(?:this\s*->\s*)?(?:Get\w*Component|GetSprite|GetMesh|GetRootComponent)\s*\(\s*\)$")
UNBIND_FUNCS = ("EndPlay", "NativeDestruct", "Deinitialize", "BeginDestroy")
# Rule L: the character shell only wires components (pipeline/roles/technical-director.md, Owns).
SHELL_CLASS = "AEllaCharacter"
SHELL_FUNCS = (SHELL_CLASS, "SetupPlayerInputComponent")
SHELL_INPUT_CALLS = ("SetupPlayerInputComponent", "AddMappingContext", "BindInput", "Cast", "CastChecked",
                     "GetController", "GetLocalPlayer", "GetSubsystem", "IsValid", "ensure", "IsLocallyControlled")
CALL_RE = re.compile(r"\b(\w+)\s*(?:<[^;<>()]*>)?\s*\(")
CONTROL_WORDS = ("if", "for", "while", "switch", "return", "sizeof", "catch")

REFLECT_MACRO_RE = re.compile(r"\b(UCLASS|USTRUCT|UINTERFACE)\s*\(((?:[^()]|\([^()]*\))*)\)\s*$")
UENUM_MACRO_RE = re.compile(r"\bUENUM\s*\(((?:[^()]|\([^()]*\))*)\)\s*$")
CLASS_DEF_RE = re.compile(r"\b(class|struct)\s+((?:\w+_API\s+)?)(\w+)\s*(?:final\s*)?(?::\s*([^{;()]*))?\{")
ENUM_RE = re.compile(r"\benum\s+(class\s+|struct\s+)?(\w+)\s*(?::\s*([\w:]+))?\s*\{")
MEMBER_MACRO_RE = re.compile(r"\b(UPROPERTY|UFUNCTION|GENERATED_BODY|GENERATED_UCLASS_BODY|GENERATED_USTRUCT_BODY"
                             r"|UE_DEPRECATED)\s*\((?:[^()]|\([^()]*\))*\)")
ACCESS_RE = re.compile(r"\b(public|private|protected)\s*:(?!:)")
FUNC_HEAD_RE = re.compile(r"\)\s*(?:const|override|final|noexcept|&|\s)*$|\)\s*:[^;]*\)\s*$")
NUMBER_RE = re.compile(r"(?<![\w.'])(0[xX][0-9a-fA-F']+|(?:\d[\d']*\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)[fFuUlL]*(?![\w.'])")
UOBJECT_REF_RE = re.compile(r"(?<![\w:])((?:const\s+)?([UA][A-Z]\w*))\s*&(?!&)(?=\s*\w*\s*(?:[,)=]|$))", re.M)
TYPE_HELP = "U (UObject), A (Actor), F (struct or plain class), T (template), I (interface), E (enum)"
BUILTIN_TYPES = r"bool|char|int|short|long|float|double|unsigned|auto|TCHAR|ANSICHAR|u?int(?:8|16|32|64)"
# "<Type> <name>" followed by = ; , ) [ { or a single colon: a local, parameter or range-for variable.
LOCAL_DECL_RE = re.compile(r"(?<![\w:.>\-])(?:const\s+)?(?:" + BUILTIN_TYPES + r"|[A-Z]\w*(?:::\w+)*(?:\s*<[^;(){}]*>)?)"
                           r"\s*(?:const\s*)?[*&]*\s*(?:const\s+)?\b([A-Za-z_]\w*)\s*(?=[=;,)\[{]|:(?!:))")
NOT_NAMES = {"const", "override", "final", "public", "private", "protected", "virtual", "static", "mutable",
             "volatile", "return", "new", "delete", "this", "true", "false", "nullptr", "operator", "class",
             "struct", "typename", "template", "noexcept", "default", "case", "else", "sizeof", "inline"}


def is_macro_name(name):
    return name.upper() == name


def type_defs(code):
    """[(kind, name, bases, macro, name_pos, open, close)] for each class/struct definition with a body."""
    out = []
    for m in CLASS_DEF_RE.finditer(code):
        before = code[max(0, m.start() - 600):m.start()]
        if re.search(r"\benum\s*$", before):
            continue
        open_ = m.end() - 1
        close = match_close(code, open_)
        if close < 0:
            continue
        rm = REFLECT_MACRO_RE.search(before)
        out.append((m.group(1), m.group(3), m.group(4) or "", rm.group(1) if rm else None, m.start(3), open_, close))
    return out


def body_decls(code, open_, close, default_access):
    """Split a class body into its top-level declarations.
    Returns [(pos, access, text, uproperty, is_definition)] with reflection macros and access labels removed.
    uproperty is the UPROPERTY specifier text ("" for UPROPERTY()), or None when there is none."""
    out = []
    access = default_access

    def emit(seg, head, is_def):
        nonlocal access
        p = seg
        for am in ACCESS_RE.finditer(head):
            access = am.group(1)
            p = max(p, seg + am.end())
        um = re.search(r"\bUPROPERTY\s*\(((?:[^()]|\([^()]*\))*)\)", head)
        has_uprop = um.group(1) if um else None
        for mm in MEMBER_MACRO_RE.finditer(head):
            p = max(p, seg + mm.end())
        text = ACCESS_RE.sub(" ", MEMBER_MACRO_RE.sub(" ", head)).strip()
        if text:
            out.append((skip_ws(code, p), access, " ".join(text.split()), has_uprop, is_def))

    i = seg = open_ + 1
    while i < close:
        ch = code[i]
        if ch in "([":
            j = match_close(code, i)
            i = j + 1 if j > 0 else i + 1
        elif ch == "{":
            j = match_close(code, i)
            if j < 0:
                break
            head = code[seg:i]
            i = j + 1
            if FUNC_HEAD_RE.search(head):
                emit(seg, head, True)
                k = skip_ws(code, i)
                if code[k:k + 1] == ";":
                    i = k + 1
                seg = i
        elif ch == ";":
            emit(seg, code[seg:i], False)
            i += 1
            seg = i
        else:
            i += 1
    return out


def strip_angles(text):
    """Text with every balanced <...> removed, so TFunction<void()> Pending reads as a data member."""
    out, depth = [], 0
    for ch in text:
        if ch == "<":
            depth += 1
        elif ch == ">" and depth:
            depth -= 1
        elif not depth:
            out.append(ch)
    return "".join(out) if depth == 0 else text


def split_function(text):
    """For a declaration with a parameter list: (return part, name, params, tail), else None."""
    groups, depth, start = [], 0, -1
    for k, ch in enumerate(text):
        if ch == "(":
            if depth == 0:
                start = k
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start >= 0:
                groups.append((start, k))
    if not groups:
        return None
    gs, ge = groups[-1]
    nm = re.search(r"(~?\w+)\s*$", text[:gs])
    if not nm:
        return None
    return text[:nm.start()].strip(), nm.group(1), text[gs + 1:ge], text[ge + 1:]


def enclosing_call(code, pos):
    """Name of the innermost call whose argument list contains pos, or None."""
    depth = 0
    for k in range(pos - 1, -1, -1):
        ch = code[k]
        if ch in ")]}":
            depth += 1
        elif ch in "([{":
            if depth == 0:
                if ch != "(":
                    return None
                m = re.search(r"(\w+)\s*(?:<[^<>;]*>)?\s*$", code[:k])
                return m.group(1) if m else None
            depth -= 1
    return None


def lambdas(code):
    """[(pos, capture list text)] for lambda expressions (a [ in argument or assignment position)."""
    out = []
    for m in re.finditer(r"\[", code):
        k = m.start() - 1
        while k >= 0 and code[k].isspace():
            k -= 1
        if k >= 0 and code[k] not in "(,=":
            continue
        close = match_close(code, m.start())
        if close < 0:
            continue
        j = skip_ws(code, close + 1)
        if code[j:j + 1] == "(":
            pc = match_close(code, j)
            if pc < 0:
                continue
            j = skip_ws(code, pc + 1)
        sm = re.match(r"(?:mutable|constexpr|noexcept|\s)*(?:->\s*[^{;]*)?", code[j:])
        j = skip_ws(code, j + sm.end())
        if code[j:j + 1] == "{":
            out.append((m.start(), code[m.start() + 1:close]))
    return out


def block_end(code, pos):
    """End index of the outermost { } block that contains pos (the function body in a .cpp), or len(code)."""
    depth, outer = 0, None
    for k in range(pos):
        ch = code[k]
        if ch == "{":
            if depth == 0:
                outer = k
            depth += 1
        elif ch == "}":
            depth -= 1
    if outer is None or depth <= 0:
        return len(code)
    end = match_close(code, outer)
    return end if end > 0 else len(code)


def bool_selector_params(fname, params):
    """Names of by-value bool parameters, minus the forms rule J allows."""
    args = [a for a in top_level_args(params) if a]
    bools = []
    for a in args:
        decl = a.split("=", 1)[0]
        if re.search(r"\bbool\b", decl) and not re.search(r"[*&]", decl):
            nm = re.search(r"(\w+)\s*$", decl)
            bools.append(nm.group(1) if nm and nm.group(1) != "bool" else "(unnamed)")
    if not bools:
        return []
    if re.match(r"Set[A-Z]", fname) and len(args) == 1:
        return []
    if re.match(r"On[A-Z]", fname):
        return []
    return bools


def number_value(lit):
    s = lit.replace("'", "")
    try:
        return float(int(s, 16)) if s[:2].lower() == "0x" else float(s)
    except ValueError:
        return None


def function_bodies(code, name):
    """Bodies (text) of every out-of-class definition X::name(...) { ... } in code."""
    bodies = []
    for em in re.finditer(r"::\s*" + name + r"\s*\(", code):
        close = match_close(code, em.end() - 1)
        j = skip_ws(code, close + 1) if close >= 0 else -1
        if j >= 0:
            sm = re.match(r"(?:const|override|final|noexcept|\s)*", code[j:])
            j = skip_ws(code, j + sm.end())
        if j >= 0 and code[j:j + 1] == "{":
            bodies.append(code[j:match_close(code, j) + 1])
    return bodies


NONDET_RE = re.compile(r"\bFMath\s*::\s*(?:S?Rand\w*|FRand\w*|VRand\w*)\b|\bFPlatformTime\s*::\s*\w+"
                       r"|\bFDateTime\s*::\s*(?:Now|UtcNow)\b|(?<![\w:.>])s?rand\s*\(")
CONTAINER_GETTER_RE = re.compile(r"^[ \t]*(?:(?:virtual|static|inline|FORCEINLINE)\s+)*"
                                 r"(TArray|TMap|TSet|TMultiMap|TSortedMap)\s*<[^;(){}]*>\s*[&*]\s*(\w+)\s*\(", re.M)


def standard_findings(path, raw):
    """Rules w-z and A-H for one source file. Returns [(rule, line, message)]."""
    code = blank_strings(strip_comments(raw))
    is_header = path.endswith(HEADER_EXT)
    norm = path.replace(os.sep, "/")
    out = []

    def at(rule, pos, msg):
        out.append((rule, line_of(code, pos), msg))

    # w: type prefixes, and PascalCase members; A/B/C/J: const, access and bool parameters, from the same body walk
    member_names = set()
    for kind, name, bases, macro, npos, open_, close in type_defs(code):
        if macro in ("UCLASS", "UINTERFACE"):
            actor = re.search(r"\bA[A-Z]\w*", bases) is not None
            want = "A" if actor and macro == "UCLASS" else "U"
            if not re.match(want + r"[A-Z]", name):
                at("w", npos, f"{macro} '{name}' must start with {want}"
                              f"{' (it derives from an actor)' if want == 'A' else ''}")
        elif macro == "USTRUCT":
            if not re.match(r"F[A-Z]", name):
                at("w", npos, f"USTRUCT '{name}' must start with F")
        elif not re.match(r"[FTIS][A-Z]", name):
            at("w", npos, f"{kind} '{name}' has no type prefix; use {TYPE_HELP}")
        default = "public" if kind == "struct" else "private"
        settings = re.search(r"\bUDeveloperSettings\b", bases) is not None
        for pos, access, text, has_uprop, is_def in body_decls(code, open_, close, default):
            if re.match(r"(class|struct|enum|union|friend|using|typedef|static_assert|template)\b", text) \
                    or re.search(r"\boperator\b", text):
                continue
            lhs = re.sub(r"\{[^{}]*\}", " ", text.split("=", 1)[0])
            fn = split_function(text) if "(" in strip_angles(lhs) else None
            if fn:
                ret, fname, _, tail = fn
                if is_macro_name(fname) or fname in (name, "~" + name):
                    continue
                if not re.match(r"[A-Z]", fname):
                    at("w", pos, f"function '{fname}' must be PascalCase")
                if not is_header:
                    continue
                engine = re.search(r"\b(override|final)\b", tail)
                static = re.search(r"\bstatic\b", ret)
                if fname.startswith(GETTER_PREFIXES) and re.match(r"(?:Get|Is|Has|Can|Should)[A-Z0-9]", fname) \
                        and not engine and not static and not re.search(r"\bconst\b", tail):
                    at("A", pos, f"'{fname}' reads state; make it a const member function ({fname}(...) const)")
                rclean = re.sub(r"\b(virtual|static|inline|FORCEINLINE|FORCENOINLINE|explicit|constexpr|\w+_API)\b",
                                " ", ret).strip()
                if re.match(r"const\b", rclean) and not re.search(r"[*&]", rclean):
                    at("B", pos, f"'{fname}' returns '{rclean}' by value; drop the const on the return type")
                if macro == "UCLASS" and not engine and not static:
                    for pname in bool_selector_params(fname, fn[2]):
                        at("J", pos, f"'{fname}' takes bool '{pname}', which picks a behavior at the call site "
                                     f"({fname}(true)); use an enum or two functions")
                continue
            nm = re.search(r"(\w+)\s*(?:\[[^\]]*\])?\s*(?::\s*\d+)?\s*$", lhs)
            if not nm or is_macro_name(nm.group(1)):
                continue
            mname, mtype = nm.group(1), lhs[:nm.start()]
            if not mtype.strip():
                continue
            bitfield_bool = re.search(r":\s*1\s*$", lhs) and re.match(r"b[A-Z0-9]", mname)
            if not re.search(r"\bbool\b", mtype) and not bitfield_bool and not re.match(r"[A-Z][A-Za-z0-9]*$", mname):
                fixed = mname[:1].upper() + re.sub(r"_(\w)", lambda g: g.group(1).upper(), mname[1:])
                at("w", pos, f"member '{mname}' must be PascalCase ({fixed})")
                member_names.add((line_of(code, pos), mname))
            if macro == "UCLASS" and access == "public" and not settings \
                    and not re.search(r"\b(static|constexpr)\b", mtype):
                at("C", pos, f"data member '{mname}' is public{' (UPROPERTY does not change that)' if has_uprop is not None else ''}; "
                             f"make it private (protected for tuning/assets) and add a getter")
            if macro == "UCLASS" and access == "protected" and not settings \
                    and not re.search(r"\b(static|constexpr)\b", mtype) \
                    and not re.search(r"\bEdit(?:DefaultsOnly|Anywhere|InstanceOnly)\b", has_uprop or "") \
                    and not re.search(r"\bF\w*Tuning\b", mtype):
                at("C", pos, f"protected data member '{mname}' is gameplay state; make it private (protected is only "
                             f"for tuning or asset references: UPROPERTY(EditDefaultsOnly/EditAnywhere) or an F*Tuning struct)")
    # w and z: enums
    for m in ENUM_RE.finditer(code):
        name = m.group(2)
        if not re.match(r"E[A-Z]", name):
            at("w", m.start(2), f"enum '{name}' must start with E")
        if UENUM_MACRO_RE.search(code[max(0, m.start() - 400):m.start()]):
            if not (m.group(1) or "").startswith("class") or m.group(3) != "uint8":
                at("z", m.start(), f"UENUM '{name}' must be 'enum class {name} : uint8'")
        elif not m.group(1):
            at("z", m.start(), f"plain enum '{name}'; use 'enum class {name}' (scoped, no implicit int)")
    for m in re.finditer(r"\benum\s*(?::\s*[\w:]+\s*)?\{", code):
        at("z", m.start(), "unnamed enum; use an enum class, or static constexpr for a constant")
    # w: locals and parameters
    for m in LOCAL_DECL_RE.finditer(code):
        name = m.group(1)
        ls = code.rfind("\n", 0, m.start()) + 1
        if name in NOT_NAMES or is_macro_name(name) or re.match(r"[A-Z][A-Za-z0-9]*$|b[A-Z0-9][A-Za-z0-9]*$", name) \
                or code[ls:m.start()].lstrip().startswith("#"):
            continue
        if re.match(r"(?:const\s+)?bool\b", m.group(0)):
            continue  # bools are rule n
        line = line_of(code, m.start(1))
        if (line, name) in member_names:
            continue
        fixed = name[:1].upper() + re.sub(r"_(\w)", lambda g: g.group(1).upper(), name[1:])
        at("w", m.start(1), f"local or parameter '{name}' must be PascalCase ({fixed})")
    # x: deferred lambdas capturing by reference or raw this (inline, or stored in a variable first)
    for pos, caps in lambdas(code):
        call = enclosing_call(code, pos)
        where = f"lambda in {call}"
        if call not in DEFERRED_CALLS:
            stored = re.search(r"\bauto\s*&{0,2}\s*(\w+)\s*=\s*$", code[max(0, pos - 200):pos])
            if not stored:
                continue
            fn_var = stored.group(1)
            later = re.search(r"\b(" + "|".join(DEFERRED_CALLS) + r")\s*\([^;]*\b" + fn_var + r"\b",
                              code[pos:block_end(code, pos)])
            if not later:
                continue
            call = later.group(1)
            where = f"lambda '{fn_var}' (passed to {call} later)"
        for item in top_level_args(caps):
            if item.startswith("&"):
                at("x", pos, f"{where} captures '{item}' by reference; it runs later, after locals are gone. "
                             f"Capture by value")
            elif item == "this":
                at("x", pos, f"{where} captures raw 'this'; use CreateWeakLambda(this, ...) or CreateUObject")
            elif item == "=":
                at("x", pos, f"{where} captures with [=], which also captures 'this' implicitly; "
                             f"list each capture by value and use CreateWeakLambda(this, ...) for members")
    # y: auto
    for m in re.finditer(r"\bauto\b", code):
        if re.match(r"\s*&{0,2}\s*\w+\s*=\s*\[", code[m.end():]):
            continue  # a lambda variable
        call_open = None
        depth = 0
        for k in range(m.start() - 1, -1, -1):
            ch = code[k]
            if ch == ")":
                depth += 1
            elif ch == "(":
                if depth == 0:
                    call_open = k
                    break
                depth -= 1
            elif ch in ";{}":
                break
        if call_open is not None and re.search(r"\bfor\s*$", code[:call_open]):
            close = match_close(code, call_open)
            if close > 0 and re.search(r"(?<!:):(?!:)", code[call_open:close]) and ";" not in code[call_open:close]:
                continue  # range-based for
        at("y", m.start(), "'auto'; write the type (allowed only for lambda variables and range-based for)")
    # D: UObject passed by reference
    if is_header:
        for m in UOBJECT_REF_RE.finditer(code):
            if is_macro_name(m.group(2)):
                continue
            stmt_end = code.find(";", m.end())
            if stmt_end > 0 and re.search(r"\)\s*(?:const\s*)?override\b", code[m.end():stmt_end]):
                continue   # an engine override must keep the engine's signature (UWorldSubsystem::OnWorldBeginPlay(UWorld&))
            at("D", m.start(), f"'{m.group(1)}&' passes a UObject by reference; pass a pointer ({m.group(2)}*)")
    # E: macro names
    for m in re.finditer(r"^\s*#\s*define\s+(\w+)", code, re.M):
        name = m.group(1)
        if name in MACRO_ALLOWED or (name.startswith(MACRO_PREFIXES) and re.match(r"[A-Z0-9_]+$", name)):
            continue
        at("E", m.start(1), f"#define {name}: project macros are ALL_CAPS and start with {' or '.join(MACRO_PREFIXES)}")
    if not is_header:
        # F: delegates bound on another object are removed in EndPlay
        bound = []
        for m in re.finditer(r"(?:->|\.)\s*(\w+)\s*\.\s*(" + "|".join(DELEGATE_ADD) + r")\s*\(", code):
            op = m.start()
            ls = max(code.rfind(";", 0, op), code.rfind("{", 0, op), code.rfind("}", 0, op)) + 1
            obj = code[ls:op].strip()
            own = re.match(r"(?:this\s*->\s*)?(\w+)$", obj)
            if own and re.search(r"\b" + own.group(1) + r"\s*=\s*CreateDefaultSubobject\b", code):
                continue  # own subobject: dies with us
            if OWN_COMPONENT_GETTERS.match(obj):
                continue
            bound.append((m.start(1), m.group(1), m.group(2)))
        if bound:
            unbind = "".join(b for fn in UNBIND_FUNCS for b in function_bodies(code, fn))
            for pos, dname, how in bound:
                if not re.search(r"\b" + dname + r"\s*\.\s*(Remove\w*|Clear)\s*\(", unbind):
                    at("F", pos, f"{dname}.{how} binds onto another object, but no ::EndPlay here removes it "
                                 f"({dname}.RemoveDynamic / RemoveAll(this))")
        # G: unnamed numbers in logic
        if "/Tests/" not in norm:
            for m in NUMBER_RE.finditer(code):
                ls = code.rfind("\n", 0, m.start()) + 1
                if code[ls:m.start()].lstrip().startswith("#"):
                    continue
                val = number_value(m.group(1))
                if val is None or val in ALLOWED_NUMBERS:
                    continue
                ss = max(code.rfind(";", 0, m.start()), code.rfind("{", 0, m.start()), code.rfind("}", 0, m.start())) + 1
                named = re.match(r"\s*(?:static\s+)?(?:constexpr|const)\b[^;]*=", code[ss:m.start()])
                at("G", m.start(), f"number {m.group(0)} in .cpp logic{' (a const in a .cpp is still hard-coded)' if named else ''}; "
                                   f"read it from the component's F<Comp>Tuning via GetDefault<UUmbrellaTuning>(), "
                                   f"or put a true constant in a header as static constexpr")
    # L: the character shell only wires (constructor + SetupPlayerInputComponent)
    if not is_header:
        for m in re.finditer(r"\b" + SHELL_CLASS + r"\s*::\s*(~?\w+)\s*\(", code):
            close = match_close(code, m.end() - 1)
            if close < 0:
                continue
            j = skip_ws(code, close + 1)
            sm = re.match(r"(?:const|override|final|noexcept|\s)*", code[j:])
            j = skip_ws(code, j + sm.end())
            if code[j:j + 1] == ":" and m.group(1) == SHELL_CLASS:
                j = code.find("{", j)
            if j < 0 or code[j:j + 1] != "{":
                continue  # a call or a declaration, not a definition
            name, body = m.group(1), code[j:match_close(code, j) + 1]
            if name not in SHELL_FUNCS:
                at("L", m.start(), f"{SHELL_CLASS}::{name}: the character shell only wires components (constructor and "
                                   f"SetupPlayerInputComponent); move this logic into the component that owns it")
                continue
            for cm in CALL_RE.finditer(body):
                call = cm.group(1)
                if call in CONTROL_WORDS or is_macro_name(call):
                    continue
                if name == SHELL_CLASS and call != "BindAction":
                    continue
                if name == "SetupPlayerInputComponent" and call in SHELL_INPUT_CALLS:
                    continue
                at("L", j + cm.start(), f"{SHELL_CLASS}::{name} calls {call}; the shell only adds the mapping context "
                                        f"and calls each component's BindInput (the component binds its own actions)")
    # H: dead zones in C++
    for m in re.finditer(r"\b\w*DeadZone\w*\b", code):
        at("H", m.start(), f"'{m.group(0)}': stick dead zones live in the IA_Move Dead Zone modifier, never in C++")
    # N: determinism (GDD QA-08): no wall clock or unseeded random in gameplay code
    if not re.search(r"(^|/)(Tests|Harness)/", norm):
        for m in NONDET_RE.finditer(code):
            at("N", m.start(), f"'{m.group(0).strip()}' makes a run unrepeatable: use world time (GetWorld()->GetTimeSeconds()) "
                               f"and the seeded FRandomStream from the preset (GDD QA-08)")
    # O: mutable static state survives between PIE runs
    for m in re.finditer(r"\bstatic\b", code):
        before = code[max(0, m.start() - 12):m.start()]
        if re.search(r"\b(const|constexpr)\s*$", before):
            continue
        rest = code[m.end():m.end() + 400]
        stop = re.search(r"[;{(=]", rest)
        if not stop or stop.group(0) == "(":
            continue
        head = rest[:stop.start()]
        if re.search(r"\b(const|constexpr|consteval|constinit|class|struct|enum|union|operator)\b", head) \
                or len(re.findall(r"\w+", head)) < 2:
            continue
        at("O", m.start(), f"mutable static '{' '.join(head.split())}': PIE keeps the module loaded, so it carries into "
                           f"the next run; keep the state on a component, the GameMode or a subsystem (or make it constexpr)")
    # P: a getter that hands out a writable container
    if is_header:
        for m in CONTAINER_GETTER_RE.finditer(code):
            at("P", m.start(), f"'{m.group(2)}' returns a writable {m.group(1)}; return const& or a copy so only the owner writes it")
    return out


def forward_decl_findings(header, code, includes, project_types):
    """Rule I: a header includes a project header but uses its types only by pointer or reference."""
    out = []
    for inc, ln, target in includes:
        names = [n for n in project_types.get(target, ()) if re.search(r"\b" + n + r"\b", code)]
        if not names:
            continue
        ptr_only = True
        for n in names:
            for um in re.finditer(r"\b" + n + r"\b", code):
                before = code[max(0, um.start() - 40):um.start()]
                after = code[um.end():um.end() + 3]
                if re.match(r"\s*[*&]", after) or re.search(r"\b(class|struct)\s+$", before) \
                        or re.search(r"\b(" + "|".join(PTR_WRAPPERS) + r")\s*<\s*$", before):
                    continue
                ptr_only = False
                break
            if not ptr_only:
                break
        if ptr_only:
            out.append((ln, f'"{inc}" is only used for {", ".join(names)} by pointer or reference; '
                            f'forward-declare (class {names[0]};) and include it in the .cpp'))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--rules", default="", help="only report these rule letters, e.g. hijk (default: all)")
    a = ap.parse_args(argv)
    problems = check(a.root, with_k=True if "K" in a.rules else None)
    if problems is None:
        print(f"module_check: SKIP no Source/ folder under {a.root}")
        return 2
    if a.rules:
        problems = [p for p in problems if p[0] in a.rules]
    for rule, where, msg in problems:
        print(f"[{rule}] {where}: {msg}")
    print(f"module_check: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

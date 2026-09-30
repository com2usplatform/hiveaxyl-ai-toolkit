# Hive SDK v4 Flow

> Read this only when SKILL.md determined that the repository uses Hive SDK v4. Do not apply it together with the Axyl SDK flow.

This document defines the integration gate, automatic collection scope, and code generation differences specific to v4.
Event design follows the event design and code generation rules, and the send rules follow the SDK log send rules.

## 1. Integration gate

Apply only the checklist for the game engine or development approach identified in Phase 1. If a required item is missing, exclude
that development environment from code generation. Confirm that the following three pieces of evidence connect for the actual build target.

1. The SDK dependency or plugin
2. The hive_config.xml or runtime configuration that determines the App ID
3. The per-environment lifecycle integration and AuthV4.setup-family initialization

Paths and API names can differ with the installation form and SDK configuration. Do not rule something out merely because a single
string is absent — look for equivalent dependency, configuration, and initialization evidence. Conversely, do not judge integration
complete from a configuration file or an SDK folder alone.

Common App ID determination:

- Prefer hive_config.xml's appId or the repository's equivalent runtime configuration value.
- With no explicit value, check the official defaults — the Android Package Name, the iOS Bundle ID, or the Windows Application ID —
  in the target build settings.
- An empty value, a sample, or a placeholder is a failure. Whether the obtained value is actually registered for the project is
  checked against list_projects in Phase 3.

### Unity

| Item | Check criterion | Required by the gate |
|------|-----------|------|
| SDK itself | Assets/Hive_SDK_v4 or Assets/Hive_SDK plus actual Hive type references | Yes |
| App ID | The target build's hive_config.xml, runtime configuration, or the official platform default | Yes |
| Initialization | AuthV4.setup called in the app startup flow, handling the result's success, needExit, and failure branches | Yes |
| Send API | Confirm the Analytics.sendAnalyticsLog symbol and payload type before generating code | No |

The Unity Android configuration is usually in one of these.

- Assets/HiveSDK/hive.androidlib/src/main/res/raw/hive_config.xml
- Assets/Plugins/Android/res/raw/hive_config.xml

The Unity iOS configuration is usually at Assets/Plugins/iOS/hive_config.xml. Treat as required only the configuration
corresponding to the actual build target.

### Android Native

| Item | Check criterion | Required by the gate |
|------|-----------|------|
| SDK dependency | Gradle's com.com2us.android.hive:hive-sdk-bom + hive-sdk, or an equivalent local distribution | Yes |
| App ID | app/src/main/res/raw/hive_config.xml, an equivalent path, runtime configuration, or the applicationId default | Yes |
| lifecycle | The entry Activity forwards HiveActivity's lifecycle callbacks | Yes |
| Initialization | A com.hive.AuthV4.setup call with success, needExit, and failure handling | Yes |
| Send API | Confirm Analytics.sendAnalyticsLog and the Map<String, Object> contract before generating code | No |

Do not hardcode one example artifact coordinate as a required condition. The coordinate can differ with the distribution method, so
judge from both the actual dependency declaration and the imported Hive classes. If some HiveActivity callbacks are missing, do not
judge Android integration complete even when the SDK files are present.

### iOS Native

| Item | Check criterion | Required by the gate |
|------|-----------|------|
| SDK link | The CocoaPods HiveSDK-iOS source and Hive feature pods, the HiveSDK-iOS-SPM package, or an equivalent framework | Yes |
| SDK import | A HIVEService import, or an equivalent Hive module reference for the installed SDK | Yes |
| App ID | hive_config.xml in the Xcode resources, runtime configuration, or the Bundle ID default | Yes |
| lifecycle | AppDelegate's didFinishLaunchingWithOptions forwards to HIVEAppDelegate | Yes |
| Initialization | A Swift AuthV4Interface.setup or Objective-C HIVEAuthV4 setup call with result handling | Yes |
| Send API | Confirm HIVEAnalytics sendAnalyticsLog and the NSMutableDictionary contract before generating code | No |

Camera, photo, and tracking permission strings are app settings needed when using those features, not an Analytics send gate, so do
not treat them as required items.

### Unreal Engine

Apply the same judgment axes to an Unreal Engine project, but confirm that the SDK package is the one for that engine.

| Item | Check criterion | Required by the gate |
|------|-----------|------|
| Plugin | Plugins/HIVESDK and the Hive plugin enabled in the .uproject/.uplugin | Yes |
| Module dependency | HIVESDK included in the game module's Build.cs PublicDependencyModuleNames | Yes |
| Platform module | The HiveSDKAndroid, HiveSDKiOS, or HiveSDKWindows source module matching the target | Yes |
| App ID | The ThirdParty target platform's hive_config.xml, runtime configuration, or the platform default | Yes |
| Initialization | An FHiveAuthV4::Setup call with IsSuccess, NeedExit, and failure handling | Yes |
| Send API | Confirm FHiveAnalytics::SendAnalyticsLog and the FJsonObject contract before generating code | No |

The official default paths for Unreal configuration files:

    Plugins/HIVESDK/Source/HIVESDK/ThirdParty/android/resource/res/raw/hive_config.xml
    Plugins/HIVESDK/Source/HIVESDK/ThirdParty/iOS/resource/hive_config.xml
    Plugins/HIVESDK/Source/HIVESDK/ThirdParty/Windows/config/hive_config.xml

Native C++ (other than Unreal) currently has no checklist, so do not generate code — explain the supported scope.

### Gate output

For each development environment, report the SDK type evidence, dependencies, App ID determination path, lifecycle, and
initialization, along with the files and lines.
If hive_config.xml is absent, do not immediately conclude v4 is not integrated — check the runtime configuration and the platform
defaults, then check for Axyl signals as well.

Example checks:

    rg -n 'Hive_SDK_v4|Hive_SDK|AuthV4\.setup|sendAnalyticsLog' Assets -g '*.cs'
    rg -n 'hive-sdk-bom|com\.com2us\.android\.hive:hive-sdk|HiveActivity|AuthV4\.setup' . -g '*.gradle' -g '*.kts' -g '*.java' -g '*.kt'
    rg -n 'HiveSDK-iOS|HIVEService|HIVEAppDelegate|AuthV4Interface\.setup|HIVEAuthV4.*setup|sendAnalyticsLog' . -g 'Podfile' -g 'Package.resolved' -g '*.swift' -g '*.[hm]'
    rg -n 'HIVESDK|FHiveAuthV4::Setup|FHiveAnalytics::SendAnalyticsLog' . -g '*.Build.cs' -g '*.uproject' -g '*.uplugin' -g '*.[ch]pp' -g '*.h'

Use the official Analytics documentation only as evidence for confirming the API symbols and call contracts per development
environment. Do not copy that documentation's legacy category payload examples — apply this skill's eventName-based payload and the
SDK log send rules.

Official documentation references:

- Unity: [Install](https://developers.hiveplatform.ai/en/latest/dev/overview/getting-started/install/unity-install/),
  [Basic configuration](https://developers.hiveplatform.ai/en/latest/dev/overview/basic-config/unity-basic-config/)
- Android Native: [Install](https://developers.hiveplatform.ai/en/latest/dev/overview/getting-started/install/android-install/),
  [Basic configuration](https://developers.hiveplatform.ai/en/latest/dev/overview/basic-config/android-basic-config/)
- iOS Native: [Install](https://developers.hiveplatform.ai/en/latest/dev/overview/getting-started/install/ios-install/),
  [Basic configuration](https://developers.hiveplatform.ai/en/latest/dev/overview/basic-config/ios-basic-config/)
- Unreal Engine: [Install guide](https://developers.hiveplatform.ai/en/latest/dev/overview/getting-started/install/ue4-install/),
  [Additional install guide](https://developers.hiveplatform.ai/en/latest/dev/overview/getting-started/install/ue5-install/)
- [Hive SDK initialization](https://developers.hiveplatform.ai/en/latest/dev/initializing-hive/)
- [Android post-install lifecycle](https://developers.hiveplatform.ai/en/latest/dev/overview/getting-started/post-install/android-post-install/)
- [iOS post-install lifecycle](https://developers.hiveplatform.ai/en/latest/dev/overview/getting-started/post-install/ios-post-install/)
- [Hive SDK Analytics sending](https://developers.hiveplatform.ai/en/latest/dev/analytics/hive-send-log/hivesdk/)

## 2. SDK v4 auto-collected properties

SDK v4 game code sends only eventName among the required properties directly.
The SDK fills in userId, deviceId, identifierProvider, appId or appIdGroup, and eventTime.

Representative properties the SDK collects when sending a client log (ingested into eventAttributes):

    vid, uid, did, vid_type, guid, analytics_id
    server_id, is_hive_time, model, os, os_version, cpu
    language, device_country, hive_country, game_language
    app_version, app_version_display, sdk_version, interface_version
    build_time, channel, market, company, companyIndex
    age_gate_u13, is_url_encode, timezone

If the game puts in the same name, the game's value can overwrite the SDK's.
Do not send it unless the event definition requires it and there is evidence that the game's value is more accurate.
`guid` is the exception: the game generates and sends it per event for runtime diagnostics, and overwriting the SDK's value is allowed.

## 3. Event recommendation differences

- An ordinary recommendation queries all GAME and AUTO event templates with the Phase 3 company_cd and sdk_type=sdk_v4.
- In v4, most core events are AUTO because they can be collected automatically. Mark AUTO as `SDK automatic collection`, and find
  implementation evidence in the repository for target_collect=GAME events such as currency, content, progression, and store events.
- If there is an AUTO event enrichment request, apply the A/B procedure in the event design and code generation rules. The
  dataSource for option B's direct sends is custom_sdk.
- If the periodic session-maintenance event is AUTO, do not implement separate periodic execution logic.

### The entry funnel download section

When the event definition returns download start and completion as GAME and you have confirmed that section in the repository, use
SDK v4's entry-funnel-specific API. Do not substitute an ordinary sendAnalyticsLog payload.

| sectionId | When to call |
|-----------|-----------|
| 700 | The game data and resource download starts |
| 800 | The download completes |

    Analytics.sendUserEntryFunnelsLogs("700", null);
    Analytics.sendUserEntryFunnelsLogs("800", null);

Leave options as null/nil where the confirmed SDK examples do.
For other entry sections, check the target SDK's automatic collection status and the event definition, and do not add them arbitrarily.

## 4. Code generation

### Structure

    An existing or new central event logger
    ├─ payload builder       assembles the flat payload from eventName + guid + the event's own properties
    ├─ transport adapter     a single place that calls the SDK send
    └─ event wrapper         the per-event contract using the defined property names and types

The names above are role examples. If the repository has a central wrapper, reuse its structure and names, and only when there is
none, create an adapter matching the repository's conventions.

Required rules:

- Put only eventName, the game-generated guid, and the event's own properties in the payload.
- Preserve the numeric and string types of the event properties. Do not convert every value into a Dictionary<string, string>.
- If an existing wrapper exists, add methods to that structure.
- Use the send API signature in the form confirmed from the SDK code installed in the repository or from the official API.
- When return types differ per development environment, do not fabricate a fake bool success value — preserve the SDK's existing
  return and callback contracts.

### Send examples per development environment

The examples below are reference templates showing the payload type and the SDK call form. Use the get_event_spec results for the
actual eventName and properties, and apply them only when you have confirmed the type, method, and return or callback contract in
the target repository. Put the final SDK call in one place — the repository's central wrapper or adapter — rather than scattering
each example inline.

#### Unity (C#)

```csharp
JSONObject logData = new JSONObject();
logData.AddField("eventName", "asset_drop");
logData.AddField("guid", Guid.NewGuid().ToString("N"));
logData.AddField("level", 10);
logData.AddField("character_name", "AA");
logData.AddField("stage_id", "stage_101");

Analytics.sendAnalyticsLog(logData);
```

#### Android Native (Java)

```java
Map<String, Object> logData = new HashMap<String, Object>();
logData.put("eventName", "asset_drop");
logData.put("guid", UUID.randomUUID().toString().replace("-", ""));
logData.put("level", 10);
logData.put("character_name", "AA");
logData.put("stage_id", "stage_101");

Analytics.sendAnalyticsLog(logData);
```

Follow the repository's actual packages for the Map and HashMap imports and the Analytics class path. Even in a Kotlin project, do
not mechanically convert the Java example — confirm whether the installed SDK is callable from Kotlin and what the Java interop form is.

#### iOS Native (Objective-C)

```objc
NSMutableDictionary *logData = [[NSMutableDictionary alloc] init];
[logData setObject:@"asset_drop" forKey:@"eventName"];
[logData setObject:[[[NSUUID UUID] UUIDString] stringByReplacingOccurrencesOfString:@"-" withString:@""] forKey:@"guid"];
[logData setObject:@10 forKey:@"level"];
[logData setObject:@"AA" forKey:@"character_name"];
[logData setObject:@"stage_101" forKey:@"stage_id"];

[HIVEAnalytics sendAnalyticsLog:logData];
```

The iOS example in the source policy is Objective-C syntax, not Swift. In a Swift repository, do not convert this example and guess —
confirm the installed SDK's Swift-exposed API or its Objective-C bridge contract.

#### Unreal Engine (C++)

```cpp
#include "HiveAnalytics.h"

TSharedPtr<FJsonObject> LogData = MakeShareable(new FJsonObject);
LogData->SetStringField(TEXT("eventName"), TEXT("asset_drop"));
LogData->SetStringField(TEXT("guid"), FGuid::NewGuid().ToString(EGuidFormats::Digits));
LogData->SetNumberField(TEXT("level"), 10);
LogData->SetStringField(TEXT("character_name"), TEXT("AA"));
LogData->SetStringField(TEXT("stage_id"), TEXT("stage_101"));

FHiveAnalytics::SendAnalyticsLog(LogData);
```

Plain native C++ examples are not in the current supported scope. In all four development environments above, do not put the
SDK's auto-collected userId, deviceId, identifierProvider, appId, appIdGroup, or eventTime into the payload directly.

## 5. Code verification

- Confirm that the generated files are included in the project.
- Perform compilation or static checks in the supported development environments.
- Confirm that each event call site runs exactly once per trigger.
- Confirm that guid is generated per event and that the same value is recorded in the central send log.
- Confirm that no Axyl required properties or common device and app properties ended up in the v4 payload.
- Confirm that the download section uses the dedicated API rather than the ordinary send wrapper.

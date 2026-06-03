# Fuel Rewards® Mobile App API Discovery (Assessment Findings)

## Summary

I attempted to identify the API endpoints used by the Fuel Rewards application to retrieve location and fuel-related information. API discovery could not be completed because the application consistently crashed on the emulator before reaching a usable state.

## Environment Setup

- Genymotion Android 11 (Pixel 5)
- Root access enabled
- Frida 17.10.1
- Objection 1.12.5

## Attempts Performed

### 1) Older APK Versions

- Installed multiple older versions of the Fuel Rewards APK.
- The application launched successfully.
- However, the application immediately forced an upgrade to the latest version before allowing any interaction.

**Result:** Unable to continue testing on older versions due to mandatory update enforcement.

### 2) Latest APK Version

- Installed the latest version of the application.
- The application launched briefly and then immediately crashed.

Observed message:

```text
Fuel Rewards keeps stopping
```

### 3) Activity Launch Testing

Executed:

```bash
adb shell monkey -p com.excentus.frn.android 1
adb shell am start -n com.excentus.frn.android/com.excentus.ccmd.ui.SplashActivity
```

**Result:** Application crashed during SplashActivity initialization.

### 4) Frida Testing

Executed:

```bash
frida -U -f com.excentus.frn.android
```

Observed:

```text
java.lang.IllegalMonitorStateException
```

### 5) Objection Testing

Executed:

```bash
objection -n com.excentus.frn.android start
```

Observed:

```text
FATAL EXCEPTION: main
java.lang.IllegalMonitorStateException
```

### 6) Log Analysis

Application consistently failed during startup with:

```text
Unable to start activity:
com.excentus.ccmd.ui.SplashActivity

Caused by:
java.lang.IllegalMonitorStateException
```

## Physical Device Verification

The same application was installed on a physical Android device.

Results:

- Application launched successfully.
- Login screen was displayed.
- No crashes occurred.

However, the application requires account authentication before proceeding further. Since valid login credentials were not available, I was unable to access the location and fuel search functionality needed for API discovery.

## Findings

The issue appears to be environment-specific and reproducible only on the emulator.

Potential causes include:

1. Emulator detection.
2. Root detection.
3. Google Play Integrity / SafetyNet validation.
4. Genymotion-specific environment validation.

## Additional Notes

Additional approaches could have been explored, such as testing on alternative emulator configurations, non-rooted emulator images, ARM-based environments, SSL traffic inspection, and further runtime analysis. However, my personal laptop was experiencing significant performance and stability issues during testing, which limited further experimentation within the assignment timeline.

## Conclusion

Due to the application crashing on the emulator and requiring authenticated access on the physical device, I was unable to reach the application functionality necessary to discover and document the requested API endpoint(s). Nevertheless, the investigation confirmed that the issue is environment-specific and not related to the Frida or Objection setup itself.


import ctypes
import platform
import ssl
from ctypes import (
    CDLL,
    POINTER,
    c_bool,
    c_char_p,
    c_int32,
    c_long,
    c_uint32,
    c_ulong,
    c_void_p,
)
from ctypes.util import find_library

_mac_version = platform.mac_ver()[0]
_mac_version_info = tuple(map(int, _mac_version.split(".")))
if _mac_version_info < (10, 8):
    raise OSError(
        f"Only OS X 10.8 and newer are supported, not {_mac_version_info[0]}.{_mac_version_info[1]}"
    )


def _load_cdll(name: str, macos10_16_path: str) -> CDLL:
    """Loads a CDLL by name, falling back to known path on 10.16+"""
    try:
        # Big Sur is technically 11 but we use 10.16 due to the Big Sur
        # beta being labeled as 10.16.
        path: str | None
        if _mac_version_info >= (10, 16):
            path = macos10_16_path
        else:
            path = find_library(name)
        if not path:
            raise OSError  # Caught and reraised as 'ImportError'
        return CDLL(path, use_errno=True)
    except OSError:
        raise ImportError(f"The library {name} failed to load") from None


Security = _load_cdll(
    "Security", "/System/Library/Frameworks/Security.framework/Security"
)
CoreFoundation = _load_cdll(
    "CoreFoundation",
    "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation",
)

Boolean = c_bool
CFIndex = c_long
CFStringEncoding = c_uint32
CFData = c_void_p
CFString = c_void_p
CFArray = c_void_p
CFMutableArray = c_void_p
CFError = c_void_p
CFType = c_void_p
CFTypeID = c_ulong
CFTypeRef = POINTER(CFType)
CFAllocatorRef = c_void_p

OSStatus = c_int32

CFErrorRef = POINTER(CFError)
CFDataRef = POINTER(CFData)
CFStringRef = POINTER(CFString)
CFArrayRef = POINTER(CFArray)
CFMutableArrayRef = POINTER(CFMutableArray)
CFArrayCallBacks = c_void_p

SecCertificateRef = POINTER(c_void_p)
SecPolicyRef = POINTER(c_void_p)
SecTrustRef = POINTER(c_void_p)
SecTrustResultType = c_uint32
SecTrustOptionFlags = c_uint32

try:
    Security.SecCertificateCreateWithData.argtypes = [CFAllocatorRef, CFDataRef]
    Security.SecCertificateCreateWithData.restype = SecCertificateRef

    Security.SecCertificateCopyData.argtypes = [SecCertificateRef]
    Security.SecCertificateCopyData.restype = CFDataRef

    Security.SecCopyErrorMessageString.argtypes = [OSStatus, c_void_p]
    Security.SecCopyErrorMessageString.restype = CFStringRef

    Security.SecTrustSetAnchorCertificates.argtypes = [SecTrustRef, CFArrayRef]
    Security.SecTrustSetAnchorCertificates.restype = OSStatus

    Security.SecTrustSetAnchorCertificatesOnly.argtypes = [SecTrustRef, Boolean]
    Security.SecTrustSetAnchorCertificatesOnly.restype = OSStatus

    Security.SecTrustEvaluate.argtypes = [SecTrustRef, POINTER(SecTrustResultType)]
    Security.SecTrustEvaluate.restype = OSStatus

    Security.SecPolicyCreateSSL.argtypes = [Boolean, CFStringRef]
    Security.SecPolicyCreateSSL.restype = SecPolicyRef

    Security.SecTrustCreateWithCertificates.argtypes = [
        CFTypeRef,
        CFTypeRef,
        POINTER(SecTrustRef),
    ]
    Security.SecTrustCreateWithCertificates.restype = OSStatus

    Security.SecTrustGetTrustResult.argtypes = [
        SecTrustRef,
        POINTER(SecTrustResultType),
    ]
    Security.SecTrustGetTrustResult.restype = OSStatus

    Security.SecCopyErrorMessageString.argtypes = [OSStatus, c_void_p]
    Security.SecCopyErrorMessageString.restype = CFStringRef

    Security.SecTrustRef = SecTrustRef  # type: ignore[attr-defined]
    Security.SecTrustResultType = SecTrustResultType  # type: ignore[attr-defined]
    Security.OSStatus = OSStatus  # type: ignore[attr-defined]

    CoreFoundation.CFRelease.argtypes = [CFTypeRef]
    CoreFoundation.CFRelease.restype = None

    CoreFoundation.CFGetTypeID.argtypes = [CFTypeRef]
    CoreFoundation.CFGetTypeID.restype = CFTypeID

    CoreFoundation.CFStringCreateWithCString.argtypes = [
        CFAllocatorRef,
        c_char_p,
        CFStringEncoding,
    ]
    CoreFoundation.CFStringCreateWithCString.restype = CFStringRef

    CoreFoundation.CFStringGetCStringPtr.argtypes = [CFStringRef, CFStringEncoding]
    CoreFoundation.CFStringGetCStringPtr.restype = c_char_p

    CoreFoundation.CFStringGetCString.argtypes = [
        CFStringRef,
        c_char_p,
        CFIndex,
        CFStringEncoding,
    ]
    CoreFoundation.CFStringGetCString.restype = c_bool

    CoreFoundation.CFDataCreate.argtypes = [CFAllocatorRef, c_char_p, CFIndex]
    CoreFoundation.CFDataCreate.restype = CFDataRef

    CoreFoundation.CFDataGetLength.argtypes = [CFDataRef]
    CoreFoundation.CFDataGetLength.restype = CFIndex

    CoreFoundation.CFDataGetBytePtr.argtypes = [CFDataRef]
    CoreFoundation.CFDataGetBytePtr.restype = c_void_p

    CoreFoundation.CFArrayCreate.argtypes = [
        CFAllocatorRef,
        POINTER(CFTypeRef),
        CFIndex,
        CFArrayCallBacks,
    ]
    CoreFoundation.CFArrayCreate.restype = CFArrayRef

    CoreFoundation.CFArrayCreateMutable.argtypes = [
        CFAllocatorRef,
        CFIndex,
        CFArrayCallBacks,
    ]
    CoreFoundation.CFArrayCreateMutable.restype = CFMutableArrayRef

    CoreFoundation.CFArrayAppendValue.argtypes = [CFMutableArrayRef, c_void_p]
    CoreFoundation.CFArrayAppendValue.restype = None

    CoreFoundation.CFArrayGetCount.argtypes = [CFArrayRef]
    CoreFoundation.CFArrayGetCount.restype = CFIndex

    CoreFoundation.CFArrayGetValueAtIndex.argtypes = [CFArrayRef, CFIndex]
    CoreFoundation.CFArrayGetValueAtIndex.restype = c_void_p

    CoreFoundation.CFErrorGetCode.argtypes = [CFErrorRef]
    CoreFoundation.CFErrorGetCode.restype = CFIndex

    CoreFoundation.CFErrorCopyDescription.argtypes = [CFErrorRef]
    CoreFoundation.CFErrorCopyDescription.restype = CFStringRef

    CoreFoundation.kCFAllocatorDefault = CFAllocatorRef.in_dll(  # type: ignore[attr-defined]
        CoreFoundation, "kCFAllocatorDefault"
    )
    CoreFoundation.kCFTypeArrayCallBacks = c_void_p.in_dll(  # type: ignore[attr-defined]
        CoreFoundation, "kCFTypeArrayCallBacks"
    )

    CoreFoundation.CFTypeRef = CFTypeRef  # type: ignore[attr-defined]
    CoreFoundation.CFArrayRef = CFArrayRef  # type: ignore[attr-defined]
    CoreFoundation.CFStringRef = CFStringRef  # type: ignore[attr-defined]
    CoreFoundation.CFErrorRef = CFErrorRef  # type: ignore[attr-defined]

except AttributeError:
    raise ImportError("Error initializing ctypes") from None


class CFConst:
    """CoreFoundation constants"""

    kCFStringEncodingUTF8 = CFStringEncoding(0x08000100)


def _bytes_to_cf_data_ref(value: bytes) -> CFDataRef:  # type: ignore[valid-type]
    return CoreFoundation.CFDataCreate(  # type: ignore[no-any-return]
        CoreFoundation.kCFAllocatorDefault, value, len(value)
    )


def _bytes_to_cf_string(value: bytes) -> CFString:
    """
    Given a Python binary data, create a CFString.
    The string must be CFReleased by the caller.
    """
    c_str = ctypes.c_char_p(value)
    cf_str = CoreFoundation.CFStringCreateWithCString(
        CoreFoundation.kCFAllocatorDefault,
        c_str,
        CFConst.kCFStringEncodingUTF8,
    )
    return cf_str  # type: ignore[no-any-return]


def _cf_string_ref_to_str(cf_string_ref: CFStringRef) -> str | None:  # type: ignore[valid-type]
    """
    Creates a Unicode string from a CFString object. Used entirely for error
    reporting.
    Yes, it annoys me quite a lot that this function is this complex.
    """

    string = CoreFoundation.CFStringGetCStringPtr(
        cf_string_ref, CFConst.kCFStringEncodingUTF8
    )
    if string is None:
        buffer = ctypes.create_string_buffer(1024)
        result = CoreFoundation.CFStringGetCString(
            cf_string_ref, buffer, 1024, CFConst.kCFStringEncodingUTF8
        )
        if not result:
            raise OSError("Error copying C string from CFStringRef")
        string = buffer.value
    if string is not None:
        string = string.decode("utf-8")
    return string  # type: ignore[no-any-return]


def _der_certs_to_cf_cert_array(certs: list[bytes]) -> CFMutableArrayRef:  # type: ignore[valid-type]
    """Builds a CFArray of SecCertificateRefs from a list of DER-encoded certificates.
    Responsibility of the caller to call CoreFoundation.CFRelease on the CFArray.
    """
    cf_array = CoreFoundation.CFArrayCreateMutable(
        CoreFoundation.kCFAllocatorDefault,
        0,
        ctypes.byref(CoreFoundation.kCFTypeArrayCallBacks),
    )
    if not cf_array:
        raise MemoryError("Unable to allocate memory!")

    for cert_data in certs:
        cf_data = None
        sec_cert_ref = None
        try:
            cf_data = _bytes_to_cf_data_ref(cert_data)
            sec_cert_ref = Security.SecCertificateCreateWithData(
                CoreFoundation.kCFAllocatorDefault, cf_data
            )
            CoreFoundation.CFArrayAppendValue(cf_array, sec_cert_ref)
        finally:
            if cf_data:
                CoreFoundation.CFRelease(cf_data)
            if sec_cert_ref:
                CoreFoundation.CFRelease(sec_cert_ref)

    return cf_array  # type: ignore[no-any-return]


def _configure_context(ctx: ssl.SSLContext) -> None:
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE


def _verify_peercerts_impl(
    ssl_context: ssl.SSLContext,
    cert_chain: list[bytes],
    server_hostname: str | None = None,
) -> None:
    certs = None
    policy = None
    trust = None
    cf_error = None
    try:
        if server_hostname is not None:
            cf_str_hostname = None
            try:
                cf_str_hostname = _bytes_to_cf_string(server_hostname.encode("ascii"))
                policy = Security.SecPolicyCreateSSL(True, cf_str_hostname)
            finally:
                if cf_str_hostname:
                    CoreFoundation.CFRelease(cf_str_hostname)
        else:
            policy = Security.SecPolicyCreateSSL(True, None)

        certs = None
        try:
            certs = _der_certs_to_cf_cert_array(cert_chain)

            # Now that we have certificates loaded and a SecPolicy
            # we can finally create a SecTrust object!
            trust = Security.SecTrustRef()
            status = Security.SecTrustCreateWithCertificates(
                certs, policy, ctypes.byref(trust)
            )
            assert status == 0  # TODO: Check status

        finally:
            # The certs are now being held by SecTrust so we can
            # release our handles for the array.
            if certs:
                CoreFoundation.CFRelease(certs)

        # If there are additional trust anchors to load we need to transform
        # the list of DER-encoded certificates into a CFArray. Otherwise
        # pass 'None' to signal that we only want system / fetched certificates.
        ctx_ca_certs_der: list[bytes] | None = ssl_context.get_ca_certs(binary_form=True)  # type: ignore[assignment]
        if ctx_ca_certs_der:
            ctx_ca_certs = None
            try:
                ctx_ca_certs = _der_certs_to_cf_cert_array(cert_chain)
                status = Security.SecTrustSetAnchorCertificates(trust, ctx_ca_certs)
            finally:
                if ctx_ca_certs:
                    CoreFoundation.CFRelease(ctx_ca_certs)
        else:
            status = Security.SecTrustSetAnchorCertificates(trust, None)
        assert status == 0  # TODO: Check status

        cf_error = CoreFoundation.CFErrorRef()
        sec_trust_eval_result = Security.SecTrustEvaluateWithError(
            trust, ctypes.byref(cf_error)
        )
        # sec_trust_eval_result is a bool (0 or 1)
        # where 1 means that the certs are trusted.
        if sec_trust_eval_result == 1:
            is_trusted = True
        elif sec_trust_eval_result == 0:
            is_trusted = False
        else:
            raise ssl.SSLError(
                f"Unknown result from Security.SecTrustEvaluateWithError: {sec_trust_eval_result!r}"
            )

        if not is_trusted:
            cf_error_code = CoreFoundation.CFErrorGetCode(cf_error)
            cf_error_string_ref = None
            try:
                cf_error_string_ref = CoreFoundation.CFErrorCopyDescription(cf_error)

                # Can this ever return 'None' if there's a CFError?
                cf_error_message = (
                    _cf_string_ref_to_str(cf_error_string_ref)
                    or "Certificate verification failed"
                )

                # TODO: Not sure if we need the SecTrustResultType for anything?
                # We only care whether or not it's a success or failure for now.
                sec_trust_result_type = Security.SecTrustResultType()
                status = Security.SecTrustGetTrustResult(
                    trust, ctypes.byref(sec_trust_result_type)
                )
                assert status == 0  # TODO: Check status

                err = ssl.SSLCertVerificationError(cf_error_message)
                err.verify_message = cf_error_message
                err.verify_code = cf_error_code
                raise err
            finally:
                if cf_error_string_ref:
                    CoreFoundation.CFRelease(cf_error_string_ref)

    finally:
        if policy:
            CoreFoundation.CFRelease(policy)
        if trust:
            CoreFoundation.CFRelease(trust)

# FFmpeg Multi-Camera DeepLabCut Optimization

This document contains comprehensive information about multi-camera recording optimization, based on the blog post "Cameras" by breq.dev (https://breq.dev/2023/06/21/cameras).

## Overview

This guide covers the complete pipeline for multi-camera recording systems, from camera selection to video streaming protocols. It's particularly relevant for DeepLabCut and other computer vision applications that require synchronized multi-camera video recording.

## Camera Types and Considerations

### USB Cameras (Recommended for Multi-Camera Setups)

**Pros:**
- Cable and connector are durable but not too bulky
- Standard software support across platforms
- Small modules available with standardized mounting holes from Arducam, ELP, etc.
- Scalable with proper USB controller management

**Cons:**
- Some overhead compared with CSI
- USB bandwidth limitations (see below)

### USB Bandwidth Management

#### Bandwidth Math
For 640x480 resolution at 30 fps in YUYV format:
- Single frame: 640×480×16 = 4,915,200 bits
- Per second: 4,915,200×30 = 147,456,000 bit/s ≈ 147 Mbit/s ≈ 18.4 MByte/s

#### USB 2.0 Limitations
- Theoretical maximum: 480 Mbit/s
- Practical maximum after overhead: **53.2 MByte/s**
- This means you can typically run **2-3 cameras** per USB controller

#### USB 3.0 Considerations
USB 3.0 does NOT help with USB 2.0 cameras because:
- USB 3.0 cables contain separate USB 2.0 and USB 3.0 wiring
- USB 2.0 cameras only use the USB 2.0 portion
- Bandwidth limitations remain the same

#### Solutions for USB Bandwidth Issues

1. **Add more USB controllers**: Use PCIe expansion cards with multiple independent USB controllers
2. **Use MJPG encoding**: Reduces bandwidth requirements (allows 3 cameras per controller vs 2)
3. **Careful controller planning**: Distribute cameras across different USB controllers
4. **Driver tweaks**: Use `UVC_QUIRKS_FIX_BANDWIDTH` for better bandwidth calculation

## Video Encoding

### H.264 Encoding Parameters

**Key factors to tune:**
- **Bandwidth**: Amount of video data per second (recommend 1 Mbps per 480p stream)
- **Keyframe interval**: Time between I-frames (recommend 30 seconds for balance)

**Hardware vs Software Encoding:**
- Hardware encoding is essential for multiple streams
- Software encoding may not keep up with many simultaneous streams

## Streaming Protocols

### Real-time Transport Protocol (RTP)
- Sends data over UDP for low latency
- Simple but requires manual port management
- Example GStreamer pipeline:
```bash
gst-launch-1.0 videotestsrc ! video/x-raw,rate=30,width=640,height=480 ! x264enc tune=zerolatency ! rtph264pay ! udpsink host=192.168.1.11 port=9090
```

### Real Time Streaming Protocol (RTSP)
- Built on top of RTP
- Provides automatic port management
- Standard protocol supported by many clients
- Better for production systems

### Motion JPEG (MJPG)
- Simple frame-by-frame transmission over HTTP
- Higher bandwidth usage but lower complexity
- Good for browser-based applications

## Client Applications

### Browser-Based Solutions

**Motion JPEG via multipart/x-mixed-replace:**
- Works well in browsers
- Acceptable latency for most applications
- Limited to 6 concurrent streams per domain (browser limitation)

**Workarounds for stream limit:**
- Use multiple subdomains pointing to the same server
- Modify browser settings (Firefox only)

### Native Applications

**GStreamer:**
- Most flexible solution
- Hardware acceleration support
- Can be integrated into Qt and other frameworks

**VLC:**
- Good for testing
- High latency due to buffering
- Not recommended for production low-latency applications

## Practical Recommendations for DeepLabCut

1. **Camera Setup**: Use USB cameras with MJPG encoding to maximize cameras per USB controller
2. **Hardware**: Consider USB expansion cards for more than 4-6 cameras
3. **Encoding**: Use H.264 with hardware acceleration if available
4. **Storage**: Plan for high disk space requirements (18.4 MB/s per camera at 640x480p30)
5. **Synchronization**: Consider hardware triggers or software synchronization methods

## Troubleshooting Tips

- Use `lsusb -t` to identify USB controller topology
- Test cameras individually before combining
- Monitor USB bandwidth usage during recording
- Consider lower resolutions or framerates if bandwidth is insufficient
- Use MJPG mode if YUYV mode causes bandwidth issues

## References

- Original blog post: https://breq.dev/2023/06/21/cameras
- GStreamer documentation: https://gstreamer.freedesktop.org/
- USB Video Class (UVC) driver documentation
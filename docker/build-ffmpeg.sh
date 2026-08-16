#!/bin/bash
set -e

DAV1D_PREFIX=/src/relink/dav1d
OBJDIR=/src/relink/objects

# dav1d is BSD-2-Clause and the native shim is Apache/MIT-derived, so their
# source is kept private.  LGPL-2.1 section 6(a) permits the work using FFmpeg
# to be supplied as machine-readable object code.  These are the exact inputs
# used for the distributed runtime.
test -f "${DAV1D_PREFIX}/lib/libdav1d.a"
test -f "${DAV1D_PREFIX}/lib/pkgconfig/dav1d.pc"
test -f "${OBJDIR}/movi.o"

ls -R /src/dist/ffmpeg/lib || echo "Directory not found"
if [ -z "$FORCE_FFMPEG" ] && [ -f "/src/dist/ffmpeg/lib/libavformat.a" ]; then
    if [ -f "${FFMPEG_SRC}/RELEASE" ]; then
        echo "FFmpeg Source Version:"
        cat "${FFMPEG_SRC}/RELEASE"
    fi
    echo "=== FFmpeg libraries found, skipping build (set FORCE_FFMPEG=true to rebuild) ==="
else
    echo "=== Building FFmpeg for WASM (with libdav1d) ==="
    
    cd ${FFMPEG_SRC}
    
    # Clean previous build
    make clean 2>/dev/null || true
    make distclean 2>/dev/null || true

    # Set PKG_CONFIG_PATH so FFmpeg can find dav1d
    export PKG_CONFIG_PATH="${DAV1D_PREFIX}/lib/pkgconfig:${PKG_CONFIG_PATH}"
    
    # Debug: verify pkg-config can find dav1d
    echo "=== Verifying dav1d pkg-config ==="
    pkg-config --libs --cflags dav1d || echo "WARNING: pkg-config cannot find dav1d"
    
    # Configure FFmpeg for the software-playback hot path.
    # Using libdav1d for AV1 - pure software decoder that works in WASM
    # -O3 + wasm SIMD: decoding throughput takes priority over the smallest asset
    # -flto: Link-time optimization
    # Note: Using --pkg-config to use native pkg-config, and EM_PKG_CONFIG_PATH for emscripten
    EM_PKG_CONFIG_PATH="${DAV1D_PREFIX}/lib/pkgconfig" \
    PKG_CONFIG_PATH="${DAV1D_PREFIX}/lib/pkgconfig" \
    emconfigure ./configure \
        --pkg-config=pkg-config \
        --prefix=/src/dist/ffmpeg \
        --target-os=none \
        --arch=x86_32 \
        --cc=emcc \
        --cxx=em++ \
        --ar=emar \
        --ranlib=emranlib \
        --nm=emnm \
        --disable-all \
        --disable-asm \
        --disable-debug \
        --disable-programs \
        --disable-doc \
        --disable-autodetect \
        --enable-zlib \
        --enable-avcodec \
        --enable-avformat \
        --enable-avutil \
        --enable-swresample \
        --enable-swscale \
        --enable-libdav1d \
        --enable-protocol=file \
        --enable-demuxer=mov,mp4,m4a,mj2,avi,flv,matroska,webm,asf,mpegts,mpegps,mpegvideo,flac,ogg,wav,srt,ass,ssa,webvtt,iamf,apv,h264,hevc,h261,h263,av1,vvc,aac,ac3,eac3,mp3,obu,ivf,mjpeg,dv \
        --enable-decoder=h264,hevc,vc1,wmv3,vp9,vp8,libdav1d,vvc,apv,mpeg1video,mpeg2video,mpeg4,h261,h263,h263p,mjpeg,dvvideo,theora,aac,aac_latm,mp3,mp2,mp1,opus,vorbis,flac,ac3,eac3,dca,truehd,mlp,wmav2,wmapro,pcm_s16le,pcm_s24le,pcm_s16be,pcm_f32le,pcm_mulaw,pcm_alaw,subrip,ass,ssa,mov_text,pgssub,dvbsub,dvdsub,webvtt,srt \
        --enable-parser=h264,hevc,vc1,vp8,vp9,av1,vvc,apv,lcevc,mpeg4video,mpegvideo,h261,h263,mjpeg,aac,mp3,opus,vorbis,flac,hdmv_pgs_subtitle \
        --enable-bsf=aac_adtstoasc,h264_mp4toannexb,hevc_mp4toannexb,vvc_mp4toannexb,vvc_metadata,av1_metadata,av1_frame_merge,av1_frame_split,lcevc_metadata,pgs_frame_merge,iso_media_metadata_manipulator,extract_extradata,vp9_superframe \
        --extra-cflags="-O3 -flto -msimd128 -s USE_PTHREADS=0 -s USE_ZLIB=1 -D_FILE_OFFSET_BITS=64 -I${DAV1D_PREFIX}/include" \
        --extra-cxxflags="-O3 -flto -msimd128 -s USE_ZLIB=1 -D_FILE_OFFSET_BITS=64 -I${DAV1D_PREFIX}/include" \
        --extra-ldflags="-s WASM=1 -s USE_ZLIB=1 -O3 -flto -msimd128 -L${DAV1D_PREFIX}/lib"

    echo "=== Compiling FFmpeg ==="
    emmake make -j$(nproc)

    echo "=== Installing FFmpeg ==="
    emmake make install
fi

echo "=== Building movi WASM module ==="
cd /src

# Create output directory
mkdir -p /src/dist/wasm

# Build the movi WASM module with Asyncify for async I/O
# Uses custom AVIO with JavaScript callbacks instead of WORKERFS
# Enable 64-bit file offsets for files >= 2GB support
# Playback optimizations:
#   -O3: decode/render throughput over minimum binary size
#   -msimd128: portable WebAssembly SIMD in current browser engines
#   -flto: Link-time optimization for better dead code elimination
#   -s ASSERTIONS=0: Remove debug assertions
#   -s DISABLE_EXCEPTION_THROWING=1: Remove exception handling overhead
#   -s LEGACY_RUNTIME=0: Use modern, smaller Emscripten runtime
#   -g0: No debug info, no name section, no DWARF
#   -s ELIMINATE_DUPLICATE_FUNCTIONS=1: Remove duplicate function definitions
#   -s TEXTDECODER=2: Use built-in browser TextDecoder
#   -s STACK_OVERFLOW_CHECK=0: Remove stack overflow checks
#   -s SUPPORT_LONGJMP=0: Disable longjmp/setjmp support
#   -s SUPPORT_ERRNO=0: Disable errno support
#   -s ASYNCIFY_STACK_SIZE=524288: Reduce asyncify stack from 1MB to 512KB
# Relink the freshly rebuilt LGPL libraries with the supplied non-LGPL object
# files.  No proprietary/native shim source is needed for this operation.
em++ "$OBJDIR"/*.o \
    -L/src/dist/ffmpeg/lib \
    -L${DAV1D_PREFIX}/lib \
    -lavformat -lavcodec -ldav1d -lavutil -lswresample -lswscale \
    -O3 \
    -flto \
    -msimd128 \
    -fno-exceptions \
    -fno-rtti \
    -D_FILE_OFFSET_BITS=64 \
    -s WASM=1 \
    -s EXPORT_ES6=1 \
    -s MODULARIZE=1 \
    -s EXPORT_NAME="createKMediaWasmModule" \
    -s ENVIRONMENT=web,worker \
    -s INITIAL_MEMORY=64MB \
    -s MAXIMUM_MEMORY=4GB \
    -s ALLOW_MEMORY_GROWTH=1 \
    -s ASYNCIFY=1 \
    -s ASYNCIFY_STACK_SIZE=524288 \
    -s "ASYNCIFY_ADD=['movi_open','movi_read_frame','movi_seek_to','movi_thumbnail_open','movi_thumbnail_read_keyframe','movi_prefetch_subtitle_cues']" \
    -s "ASYNCIFY_IMPORTS=['js_read_async','js_seek_async','js_thumbnail_packet_ready']" \
    -s EXPORTED_RUNTIME_METHODS='["ccall", "cwrap", "FS", "stringToNewUTF8", "UTF8ToString", "lengthBytesUTF8", "addFunction", "HEAPU8", "HEAPF32"]' \
    -s EXPORTED_FUNCTIONS='["_malloc", "_free", "_movi_create", "_movi_destroy", "_movi_open", "_movi_read_frame", "_movi_seek_to", "_movi_get_duration", "_movi_get_start_time", "_movi_get_format_name", "_movi_get_metadata_title", "_movi_get_stream_count", "_movi_get_stream_info", "_movi_get_extradata", "_movi_get_attachment_count", "_movi_get_attachment_stream_index", "_movi_get_attachment_size", "_movi_get_attachment_name", "_movi_get_attachment_mime_type", "_movi_get_attachment_data", "_movi_get_chapter_count", "_movi_get_chapter_start", "_movi_get_chapter_end", "_movi_get_chapter_title", "_movi_get_chapter_id", "_movi_get_chapter_language", "_movi_get_chapter_hidden", "_movi_set_log_level", "_movi_set_file_size", "_movi_enable_decoder", "_movi_set_stream_discard", "_movi_send_packet", "_movi_receive_frame", "_movi_flush_decoder", "_movi_set_skip_frame", "_movi_decode_audio_batch", "_movi_audio_batch_samples", "_movi_audio_batch_channels", "_movi_audio_batch_sample_rate", "_movi_audio_batch_pts", "_movi_audio_batch_plane", "_movi_decode_subtitle", "_movi_get_subtitle_text", "_movi_get_subtitle_times", "_movi_get_subtitle_image_info", "_movi_get_subtitle_image_data", "_movi_free_subtitle", "_movi_prefetch_subtitle_cues", "_movi_get_prefetched_cue_count", "_movi_get_prefetched_cue", "_movi_clear_prefetched_cues", "_movi_get_frame_width", "_movi_get_frame_height", "_movi_get_frame_format", "_movi_get_frame_linesize", "_movi_get_frame_data", "_movi_get_frame_samples", "_movi_get_frame_channels", "_movi_get_frame_sample_rate", "_movi_get_frame_pts", "_movi_get_frame_rgba", "_movi_get_frame_rgba_size", "_movi_get_frame_rgba_linesize", "_movi_enable_audio_downmix", "_movi_thumbnail_create", "_movi_thumbnail_destroy", "_movi_thumbnail_open", "_movi_thumbnail_read_keyframe", "_movi_thumbnail_get_packet_data", "_movi_thumbnail_decode_frame", "_movi_thumbnail_decode_frame_yuv", "_movi_thumbnail_get_plane_data", "_movi_thumbnail_get_plane_linesize", "_movi_thumbnail_get_frame_width", "_movi_thumbnail_get_frame_height", "_movi_thumbnail_clear_buffer", "_movi_thumbnail_get_extradata", "_movi_thumbnail_get_stream_info", "_movi_stretch_new", "_movi_stretch_delete", "_movi_stretch_reset", "_movi_stretch_set_transpose_semitones", "_movi_stretch_input_latency", "_movi_stretch_output_latency", "_movi_stretch_process"]' \
    -s ASSERTIONS=0 \
    -s DISABLE_EXCEPTION_THROWING=1 \
    -s ALLOW_TABLE_GROWTH=1 \
    -s INVOKE_RUN=0 \
    -s SINGLE_FILE=0 \
    -s LEGACY_RUNTIME=0 \
    -g0 \
    -s MINIFY_HTML=0 \
    -s ELIMINATE_DUPLICATE_FUNCTIONS=1 \
    -s STACK_OVERFLOW_CHECK=0 \
    -s TEXTDECODER=2 \
    -s SUPPORT_LONGJMP=0 \
    -s SUPPORT_ERRNO=0 \
    -sUSE_ZLIB=1 \
    --closure 0 \
    -o /src/dist/wasm/kmedia-wasm.js

echo "=== Build complete ==="
ls -la /src/dist/wasm/

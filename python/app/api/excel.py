# -*- coding: utf-8 -*-
import glob
import re
import os
import sys
import xlsxwriter
import pyseq
import xlrd
import pydpx_meta
import OpenEXR
from PIL import Image
# Qt 호환성 레이어 사용
from ..utils.qt_compat import QtCore, QtGui
from .constant import *
import glob
import ffmpeg
from timecode import Timecode
from edl import Parser


def _safe_open_exr(file_path):
    """
    OpenEXR 파일을 안전하게 열기

    Returns:
        OpenEXR.InputFile 객체 또는 None (실패 시)
    """
    try:
        # 파일 존재 확인
        if not os.path.exists(file_path):
            print(f"WARNING: EXR file not found: {file_path}")
            return None

        # 파일 접근 권한 확인
        if not os.access(file_path, os.R_OK):
            print(f"WARNING: No read permission for: {file_path}")
            return None

        # OpenEXR 파일 열기
        exr = OpenEXR.InputFile(file_path)
        return exr

    except Exception as e:
        print(f"ERROR: Failed to open EXR file {file_path}: {e}")
        return None


def _safe_open_dpx(file_path):
    """
    DPX 파일을 안전하게 열기

    Returns:
        pydpx_meta.DpxHeader 객체 또는 None (실패 시)
    """
    try:
        # 파일 존재 확인
        if not os.path.exists(file_path):
            print(f"WARNING: DPX file not found: {file_path}")
            return None

        # 파일 접근 권한 확인
        if not os.access(file_path, os.R_OK):
            print(f"WARNING: No read permission for: {file_path}")
            return None

        # DPX 헤더 읽기
        dpx = pydpx_meta.DpxHeader(file_path)
        return dpx

    except Exception as e:
        print(f"ERROR: Failed to open DPX file {file_path}: {e}")
        return None


class CutItem(object):

    def __init__(self,parent=None):
        self.start_tc = ""
        self.end_tc = ""
        self.rec_start_tc = ""
        self.rec_end_tc = ""
        self.clibname = ""

class MOV_INFO:

    def __init__(self,mov_file,video_stream=None,event=None,first_start=None,clip_name=None,cutitem = None):

        self.mov_file = mov_file
        self.video_stream = video_stream
        self.event = event
        self.first_start = first_start
        self.dirname = os.path.dirname(mov_file)
        self.scan_name = os.path.basename(mov_file)
        if clip_name:
            clip_name = clip_name.split(".")
            if len(clip_name) > 1:
                self.clip_name = clip_name[0] + "."
            else:
                self.clip_name = clip_name[0]
        else:
            self.clip_name = "None"
        self.cutitem = cutitem
        self.ext = "mov"


    def master_frame(self):
        start_frame = Timecode(round(self.framerate()),str(self.first_start.rec_start_tc)).frame_number
        if start_frame > 0 and start_frame < 86400:
            return 0 
        if start_frame > 86400:
            return 86400

        return start_frame
    
    @classmethod
    def video_stream(self,mov_file):
        probe = ffmpeg.probe(mov_file)
        video_stream = next((stream for stream in probe['streams'] 
                             if stream['codec_type'] == 'video'), None)
        print(video_stream)
        print(video_stream)
        print(video_stream)
        if video_stream : 
            return video_stream
        
        return None
    
    def master_timecode(self):
        if "timecode" in self.video_stream['tags']:
            start_timecode = self.video_stream['tags']['timecode']
        else:
            start_timecode = "00:00:00:00"
        start_timecode = Timecode(round(self.framerate()),str(start_timecode))
        return str(start_timecode)

    def head(self):
        return self.scan_name
    
    def tail(self):
        return None
    
    def format(self,format_str):
        return None
    

    def frames(self):

        if self.event:
            end_timecode = str(self.event.rec_end_tc)
            end_frame = Timecode(round(self.framerate()),end_timecode).frame_number

            start_timecode = str(self.event.rec_start_tc)
            start_frame = Timecode(round(self.framerate()),start_timecode).frame_number
            duraiton = end_frame - start_frame
            return duraiton
        try:
            return self.video_stream['nb_frames']
        except :
            return self.video_stream['duration_ts']

    def start(self):
        if self.event:
            start_timecode = str(self.event.rec_start_tc)
            
            mod_start_frame = Timecode(round(self.framerate()),self.master_timecode()).frame_number
            start_frame = Timecode(round(self.framerate()),start_timecode).frame_number
            return start_frame - self.master_frame() + 1
        
        return 1
            
            

    def end(self):
        if self.event:
            end_timecode = str(self.event.rec_end_tc)
            end_frame = Timecode(round(self.framerate()),end_timecode).frame_number

            start_timecode = str(self.event.rec_start_tc)
            start_frame = Timecode(round(self.framerate()),start_timecode).frame_number
            duraiton = end_frame - start_frame

            return self.start() +  duraiton - 1
        
        return self.frames()
    
    def framerate(self):
        n ,d = self.video_stream['r_frame_rate'].split("/")
        frame_rate = float(n) / float(d)
        return frame_rate
    
    


def create_excel(path):
    print(f"[PROGRESS] ========================================")
    print(f"[PROGRESS] create_excel() START - path: {path}")
    print(f"[PROGRESS] ========================================")

    sequences = _get_sequences(path)
    print(f"[PROGRESS] Found {len(sequences)} sequences")
    movs = _get_movs(path)
    print(f"[PROGRESS] Found {len(movs)} MOV files")
    if movs:
        _create_thumbnail_for_mov(movs)
        sequences = movs + sequences
        print(f"[PROGRESS] Total sequences (with MOVs): {len(sequences)}")

    print(f"[PROGRESS] Calling _create_seq_array()...")
    array = _create_seq_array(sequences)
    print(f"[PROGRESS] _create_seq_array() returned successfully")
    print(f"[PROGRESS] Array length: {len(array)}")
    print(f"[PROGRESS] About to return from create_excel()")
    return array


def _create_thumbnail_for_mov(movs):
    
    mov_jobs = {}

    for mov in movs:
        mov_key = os.path.join(mov.dirname,mov.scan_name)
        if mov_key in mov_jobs:
            mov_jobs[mov_key].append(mov)
        else:
            mov_jobs[mov_key] = [mov]

    thumbnail_path = os.path.join(movs[0].dirname,".thumbnail")
    if not os.path.exists(thumbnail_path):
        os.makedirs(thumbnail_path)

    for mov_file in mov_jobs:
            
        thumbnail_file = os.path.join(thumbnail_path,os.path.basename(mov_file).split(".")[0]+".%04d.jpg")
        select_frames = [ mov.start() for mov in mov_jobs[mov_file]]
        select_frames = list(set(select_frames))
        select_frames.sort()
        select_frames = ["eq(n\,{})".format(frame) for frame in select_frames]
        print(len(select_frames))
        print(len(select_frames))
        print(len(select_frames))
        select_command ="+".join(select_frames)
        
        command = ['rez-env',"ffmpeg","--","ffmpeg","-y"]
        command.append("-i")
        command.append(mov_file)
        command.append("-vf")
        command.append("select='{}'".format(select_command))
        #command.append("-vframes")
        #command.append("{}".format(len(select_frames)))
        command.append("-vsync")
        command.append("0")
        command.append("-s")
        command.append("960x540")
        command.append(thumbnail_file)

        command = " ".join(command)
        print(command)
        os.system(command)

def _create_seq_array(sequences):
    print(f"[PROGRESS] _create_seq_array() START - total sequences: {len(sequences)}")
    array = []
    seq_index = 0
    for seq in sequences:
        seq_index += 1
        print(f"[PROGRESS] ========== Processing sequence {seq_index}/{len(sequences)} ==========")
        print("create dir seq info {}".format(seq.start()))
        info = []
        info.insert(MODEL_KEYS['check'], QtGui.QCheckBox())
        info.insert(MODEL_KEYS['thumbnail'],_get_thumbnail(seq,sequences))
        info.insert(MODEL_KEYS['roll'],"")
        info.insert(MODEL_KEYS['seq_name'],"")
        info.insert(MODEL_KEYS['shot_name'], "")
        info.insert(MODEL_KEYS['version'],"")
        info.insert(MODEL_KEYS['type'], "org")
        info.insert(MODEL_KEYS['scan_path'], seq.dirname)
        info.insert(MODEL_KEYS['scan_name'], seq.head())
        if _get_ext(seq) in  ["mov" , "mxf"]:
            info.insert(MODEL_KEYS['clip_name'], seq.clip_name)
        else:
            info.insert(MODEL_KEYS['clip_name'], seq.head())
        info.insert(MODEL_KEYS['pad'],seq.format('%p'))
        info.insert(MODEL_KEYS['ext'],_get_ext(seq))
        print("[PROGRESS] About to call _get_resolution()")
        info.insert(MODEL_KEYS['resolution'] , _get_resolution(seq))
        print("[PROGRESS] _get_resolution() completed, calling _get_start()")
        info.insert(MODEL_KEYS['start_frame'], _get_start(seq))
        print("[PROGRESS] _get_start() completed, calling _get_end()")
        info.insert(MODEL_KEYS['end_frame'], _get_end(seq))
        print("[PROGRESS] _get_end() completed, calling _get_duration()")
        info.insert(MODEL_KEYS['duration'],_get_duration(seq))
        print("[PROGRESS] _get_duration() completed")
        info.insert(MODEL_KEYS['retime_duration'],None)
        info.insert(MODEL_KEYS['retime_percent'],None)
        info.insert(MODEL_KEYS["retime_start_frame"],None)
        print("[PROGRESS] About to process timecodes")
        if _get_ext(seq) in  ["mov" , "mxf"]:
            if seq.cutitem:
                info.insert(MODEL_KEYS['timecode_in'],str(seq.cutitem.start_tc))
                info.insert(MODEL_KEYS['timecode_out'],str(seq.cutitem.end_tc))
            else:
                print("[PROGRESS] Calling _get_time_code() for timecode_in")
                info.insert(MODEL_KEYS['timecode_in'], _get_time_code(seq,_get_start(seq)))
                print("[PROGRESS] Calling _get_time_code() for timecode_out")
                info.insert(MODEL_KEYS['timecode_out'],_get_time_code(seq,_get_end(seq)))
        else:
            print("[PROGRESS] Calling _get_time_code() for timecode_in")
            info.insert(MODEL_KEYS['timecode_in'], _get_time_code(seq,_get_start(seq)))
            print("[PROGRESS] Calling _get_time_code() for timecode_out")
            info.insert(MODEL_KEYS['timecode_out'],_get_time_code(seq,_get_end(seq)))
        print("[PROGRESS] Timecodes completed, processing final metadata")
        info.insert(MODEL_KEYS['just_in'],_get_start(seq))
        info.insert(MODEL_KEYS['just_out'], _get_end(seq))
        print("[PROGRESS] About to call _get_framerate()")
        info.insert(MODEL_KEYS['framerate'] ,_get_framerate(seq))
        print("[PROGRESS] _get_framerate() completed")
        info.insert(MODEL_KEYS['date'] , "")
        info.insert(MODEL_KEYS['clip_tag'], "")
        array.append(info)
        print("[PROGRESS] ✓ Sequence {} processing completed".format(seq.start()))
        print(f"[PROGRESS] ========== End of sequence {seq_index}/{len(sequences)} ==========\n")

    print(f"[PROGRESS] _create_seq_array() FINISHED - processed {len(array)} sequences")
    print("[PROGRESS] About to return array from _create_seq_array()")
    return array


def _get_thumbnail(seq,sequences):
    
    


    if _get_ext(seq) in ["mov","mxf"]:
        
        

        index_search =  [ x.start() for x in sequences ]
        index_search = list(set(index_search))
        index_search.sort()
        index = index_search.index(seq.start()) + 1

        mov_file = os.path.join(seq.dirname,seq.scan_name)
        thumbnail_path = os.path.join(seq.dirname,".thumbnail")
        #if not os.path.exists(thumbnail_path):
        #    os.makedirs(thumbnail_path)
        if seq.event:
            thumbnail_file = os.path.join(thumbnail_path,seq.scan_name.split(".")[0]+".%04d.jpg"%index)
        else:
            thumbnail_file = os.path.join(thumbnail_path,seq.scan_name.split(".")[0]+".0001.jpg")
        #start_frame = seq.start()

        #command = ['rez-env',"ffmpeg","--","ffmpeg","-y"]
        #command.append("-i")
        #command.append(mov_file)
        #command.append("-vf")
        #command.append("select='gte(n\,{0})'".format(seq.start()-1))
        #command.append("-vframes")
        #command.append("1")
        #command.append("-s")
        #command.append("240x144")
        #command.append(thumbnail_file)

        #command = " ".join(command)
        #os.system(command)
        return thumbnail_file
    else:
        original_file = os.path.join(seq.dirname,
                                     seq.head()+seq.format("%p")%seq.start()+seq.tail())
        
        thumbnail_path = os.path.join(os.path.dirname(seq.dirname),".thumbnail")
        thumbnail_file = os.path.join(thumbnail_path,
                                     os.path.basename(seq.dirname)+'_'+seq.head()+seq.format("%p")%seq.start()+".jpg")
        print(thumbnail_file)
        if not os.path.exists(thumbnail_path):
            os.makedirs(thumbnail_path)

        # Rez 사용 여부에 따라 oiiotool 명령 구성
        try:
            from ...app_instance import AppInstance
            app_config = AppInstance.get_config()
            use_rez = app_config.get('rez.enabled', True) if app_config else True
        except:
            # AppInstance를 사용할 수 없으면 환경변수로 판단
            use_rez = os.environ.get('USE_REZ', '1') == '1'

        if use_rez:
            # Rez 환경에서 oiio 패키지 로드
            command = ['rez-env', 'oiio', '--', 'oiiotool']
        else:
            # 로컬 시스템의 oiiotool 직접 사용
            # oiiotool이 설치되어 있는지 확인
            import shutil
            if not shutil.which('oiiotool'):
                print(f"WARNING: oiiotool not found, skipping thumbnail generation for {original_file}")
                print("         Install OpenImageIO: brew install openimageio (macOS)")
                print("                             : sudo apt-get install openimageio-tools (Linux)")
                # 썸네일 파일이 없어도 경로만 반환 (UI에서 기본 아이콘 표시)
                return thumbnail_file
            command = ['oiiotool']

        command.append(original_file)
        command.append("--colorconvert")
        command.append("linear")
        command.append("sRGB")
        command.append("--resize")
        command.append("960x540")
        command.append("-o")
        command.append(thumbnail_file)

        command_str = " ".join(command)
        print(f"Generating thumbnail: {command_str}")

        # subprocess를 사용하여 더 안전하게 실행
        import subprocess
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"ERROR: oiiotool failed with return code {result.returncode}")
                if result.stderr:
                    print(f"       {result.stderr}")
            else:
                print(f"✓ Thumbnail created: {thumbnail_file}")
        except subprocess.TimeoutExpired:
            print(f"ERROR: oiiotool timeout for {original_file}")
        except Exception as e:
            print(f"ERROR: Failed to generate thumbnail: {e}")

        return thumbnail_file
        
def _get_duration(seq):
    print(f"[DEBUG] _get_duration() START")
    if _get_ext(seq) in ["mov","mxf"]:
        result = seq.frames()
    else:
        result = len(seq.frames())
    print(f"[DEBUG] _get_duration() END - result: {result}")
    return result

def _get_start(seq):
    print(f"[DEBUG] _get_start() START")
    result = seq.start()
    print(f"[DEBUG] _get_start() END - result: {result}")
    return result

def _get_end(seq):
    print(f"[DEBUG] _get_end() START")
    result = seq.end()
    print(f"[DEBUG] _get_end() END - result: {result}")
    return result

def _get_ext(seq):
    if not seq.tail():
        return seq.mov_file.split(".")[-1]
    return seq.tail().split(".")[-1]

def _get_time_code(seq,frame):
    print(f"[DEBUG] _get_time_code() START - frame: {frame}, ext: {_get_ext(seq)}, tail: {seq.tail()}")

    if _get_ext(seq) in ["mov","mxf"]:
        print(f"[DEBUG] _get_time_code() - Processing MOV/MXF")
        mov_file = os.path.join(seq.dirname,seq.head())
        video_stream = MOV_INFO.video_stream(mov_file)
        mov_info = MOV_INFO(mov_file,video_stream)
        if 'timecode' in mov_info.video_stream['tags']:
            start_timecode = mov_info.video_stream['tags']['timecode']
        else:
            start_timecode = "00:00:00:00"
        n ,d = mov_info.video_stream['r_frame_rate'].split("/")
        frame_rate = float(n) / float(d)
        start_timecode = Timecode(round(frame_rate),str(start_timecode))
        result = str(start_timecode + (int(frame) - 1))
        print(f"[DEBUG] _get_time_code() END - MOV/MXF result: {result}")
        return result



    if seq.tail() == ".exr":
        exr_file = os.path.join(seq.dirname,seq.head()+seq.format("%p")%frame+seq.tail())
        print(f"[DEBUG] _get_time_code() - Processing EXR: {exr_file}")
        exr = _safe_open_exr(exr_file)
        if exr is None:
            print(f"[DEBUG] _get_time_code() END - EXR open failed")
            return ""
        try:
            if "timeCode" in exr.header():
                ti = exr.header()['timeCode']
                result = "%02d:%02d:%02d:%02d"%(ti.hours,ti.minutes,ti.seconds,ti.frame)
                print(f"[DEBUG] _get_time_code() END - EXR result: {result}")
                return result
        except Exception as e:
            print(f"ERROR: Failed to read timecode from {exr_file}: {e}")
        print(f"[DEBUG] _get_time_code() END - EXR no timecode")
        return ""
    elif seq.tail() == ".dpx":
        dpx_file = os.path.join(seq.dirname,seq.head()+seq.format("%p")%frame+seq.tail())
        print(f"[DEBUG] _get_time_code() - Processing DPX: {dpx_file}")
        dpx = _safe_open_dpx(dpx_file)
        if dpx is None:
            print(f"[DEBUG] _get_time_code() END - DPX open failed")
            return ""
        try:
            result = dpx.tv_header.time_code
            print(f"[DEBUG] _get_time_code() END - DPX result: {result}")
            return result
        except Exception as e:
            print(f"ERROR: Failed to read timecode from {dpx_file}: {e}")
            print(f"[DEBUG] _get_time_code() END - DPX exception")
            return ""
    elif seq.tail() == "":
        tail = seq.head().split(".")[-1]
        if tail == "dpx":
            dpx_file = os.path.join(seq.dirname,seq.head())
            print(f"[DEBUG] _get_time_code() - Processing DPX (no tail): {dpx_file}")
            dpx = _safe_open_dpx(dpx_file)
            if dpx is None:
                print(f"[DEBUG] _get_time_code() END - DPX open failed")
                return ""
            try:
                result = dpx.tv_header.time_code
                print(f"[DEBUG] _get_time_code() END - DPX (no tail) result: {result}")
                return result
            except Exception as e:
                print(f"ERROR: Failed to read timecode from {dpx_file}: {e}")
                print(f"[DEBUG] _get_time_code() END - DPX (no tail) exception")
                return ""
        elif tail == "exr":
            exr_file = os.path.join(seq.dirname,seq.head())
            print(f"[DEBUG] _get_time_code() - Processing EXR (no tail): {exr_file}")
            exr = _safe_open_exr(exr_file)
            if exr is None:
                print(f"[DEBUG] _get_time_code() END - EXR open failed")
                return ""
            try:
                if "timeCode" in exr.header():
                    ti = exr.header()['timeCode']
                    result = "%02d:%02d:%02d:%02d"%(ti.hours,ti.minutes,ti.seconds,ti.frame)
                    print(f"[DEBUG] _get_time_code() END - EXR (no tail) result: {result}")
                    return result
            except Exception as e:
                print(f"ERROR: Failed to read timecode from {exr_file}: {e}")
            print(f"[DEBUG] _get_time_code() END - EXR (no tail) no timecode")
            return ""
    else:
        print(f"[DEBUG] _get_time_code() END - Unknown type")
        return ""

def _get_framerate(seq):
    print(f"[DEBUG] _get_framerate() START - ext: {_get_ext(seq)}, tail: {seq.tail()}")

    if _get_ext(seq) in  ["mov" , "mxf"]:
        print(f"[DEBUG] _get_framerate() - Processing MOV/MXF")
        mov_file = os.path.join(seq.dirname,seq.head())
        video_stream = MOV_INFO.video_stream(mov_file)
        mov_info = MOV_INFO(mov_file,video_stream)
        n ,d = mov_info.video_stream['r_frame_rate'].split("/")
        frame_rate = float(n) / float(d)
        print(f"[DEBUG] _get_framerate() END - MOV/MXF result: {frame_rate}")
        return frame_rate

    if seq.tail() == ".exr":
        exr_file = os.path.join(seq.dirname,seq.head()+seq.format("%p")%seq.start()+seq.tail())
        print(f"[DEBUG] _get_framerate() - Processing EXR: {exr_file}")
        exr = _safe_open_exr(exr_file)
        if exr is None:
            print(f"[DEBUG] _get_framerate() END - EXR open failed")
            return ""
        try:
            if "framesPerSecond" in exr.header():
                fr = exr.header()['framesPerSecond']
                result = float(fr.n)/float(fr.d)
                print(f"[DEBUG] _get_framerate() END - EXR result: {result}")
                return result
        except Exception as e:
            print(f"ERROR: Failed to read framerate from {exr_file}: {e}")
        print(f"[DEBUG] _get_framerate() END - EXR no framerate")
        return ""
    elif seq.tail() == ".dpx":
        dpx_file = os.path.join(seq.dirname,seq.head()+seq.format("%p")%seq.start()+seq.tail())
        print(f"[DEBUG] _get_framerate() - Processing DPX: {dpx_file}")
        dpx = _safe_open_dpx(dpx_file)
        if dpx is None:
            print(f"[DEBUG] _get_framerate() END - DPX open failed")
            return ""
        try:
            result = dpx.raw_header.TvHeader.FrameRate
            print(f"[DEBUG] _get_framerate() END - DPX result: {result}")
            return result
        except Exception as e:
            print(f"ERROR: Failed to read framerate from {dpx_file}: {e}")
            print(f"[DEBUG] _get_framerate() END - DPX exception")
            return ""
    elif seq.tail() == "":
        tail = seq.head().split(".")[-1]
        if tail == "dpx":
            dpx_file = os.path.join(seq.dirname,seq.head())
            print(f"[DEBUG] _get_framerate() - Processing DPX (no tail): {dpx_file}")
            dpx = _safe_open_dpx(dpx_file)
            if dpx is None:
                print(f"[DEBUG] _get_framerate() END - DPX open failed")
                return ""
            try:
                result = dpx.raw_header.TvHeader.FrameRate
                print(f"[DEBUG] _get_framerate() END - DPX (no tail) result: {result}")
                return result
            except Exception as e:
                print(f"ERROR: Failed to read framerate from {dpx_file}: {e}")
                print(f"[DEBUG] _get_framerate() END - DPX (no tail) exception")
                return ""
        elif tail == "exr":
            exr_file = os.path.join(seq.dirname,seq.head())
            print(f"[DEBUG] _get_framerate() - Processing EXR (no tail): {exr_file}")
            exr = _safe_open_exr(exr_file)
            if exr is None:
                print(f"[DEBUG] _get_framerate() END - EXR open failed")
                return ""
            try:
                if "framesPerSecond" in exr.header():
                    fr = exr.header()['framesPerSecond']
                    result = float(fr.n)/float(fr.d)
                    print(f"[DEBUG] _get_framerate() END - EXR (no tail) result: {result}")
                    return result
            except Exception as e:
                print(f"ERROR: Failed to read framerate from {exr_file}: {e}")
            print(f"[DEBUG] _get_framerate() END - EXR (no tail) no framerate")
            return ""
    else:
        print(f"[DEBUG] _get_framerate() END - Unknown type")
        return ""

def _get_resolution(seq):
    print(f"[DEBUG] _get_resolution() START - ext: {_get_ext(seq)}, tail: {seq.tail()}")

    if _get_ext(seq) in ["mov","mxf"]:
        print(f"[DEBUG] _get_resolution() - Processing MOV/MXF file")
        mov_file = os.path.join(seq.dirname,seq.head())
        video_stream = MOV_INFO.video_stream(mov_file)
        mov_info = MOV_INFO(mov_file,video_stream)
        width  = mov_info.video_stream['width']
        height  = mov_info.video_stream['height']
        result = "%d x %d"%(width,height)
        print(f"[DEBUG] _get_resolution() END - MOV/MXF result: {result}")
        return result

    if seq.tail() == ".exr":
        exr_file = os.path.join(seq.dirname,seq.head()+seq.format("%p")%seq.start()+seq.tail())
        print(f"[DEBUG] _get_resolution() - Processing EXR file: {exr_file}")
        exr = _safe_open_exr(exr_file)
        if exr is None:
            print(f"[DEBUG] _get_resolution() END - EXR open failed, returning empty")
            return ""
        try:
            if "dataWindow" in exr.header():
                res = exr.header()['dataWindow']
                result = "%d x %d"%(res.max.x+1,res.max.y+1)
                print(f"[DEBUG] _get_resolution() END - EXR result: {result}")
                return result
        except Exception as e:
            print(f"ERROR: Failed to read resolution from {exr_file}: {e}")
        print(f"[DEBUG] _get_resolution() END - EXR no dataWindow, returning empty")
        return ""
    elif seq.tail() == ".dpx":
        dpx_file = os.path.join(seq.dirname,seq.head()+seq.format("%p")%seq.start()+seq.tail())
        print(f"[DEBUG] _get_resolution() - Processing DPX file: {dpx_file}")
        dpx = _safe_open_dpx(dpx_file)
        if dpx is None:
            print(f"[DEBUG] _get_resolution() END - DPX open failed, returning empty")
            return ""
        try:
            width = dpx.raw_header.OrientHeader.XOriginalSize
            height = dpx.raw_header.OrientHeader.YOriginalSize
            if width == 0:
                from subprocess import check_output
                dpx_info = check_output(["rez-env", "oiio","--","iinfo",dpx_file])
                resolution_info = re.search("\d+\ x\s+\d+",dpx_info)
                if resolution_info :
                    width,height = resolution_info.group().split("x")
                    width = int(width)
                    height = int(height)
            result = '%d x %d'%(width,height)
            print(f"[DEBUG] _get_resolution() END - DPX result: {result}")
            return result
        except Exception as e:
            print(f"ERROR: Failed to read resolution from {dpx_file}: {e}")
            print(f"[DEBUG] _get_resolution() END - DPX exception, returning empty")
            return ""

    elif seq.tail() in [ '.jpg','.jpeg']:
        jpg_file = os.path.join(seq.dirname,seq.head()+seq.format("%p")%seq.start()+seq.tail())
        print(f"[DEBUG] _get_resolution() - Processing JPG file: {jpg_file}")
        jpeg = Image.open(jpg_file)
        result = '%d x %d'%(jpeg.size[0],jpeg.size[1])
        print(f"[DEBUG] _get_resolution() END - JPG result: {result}")
        return result
    elif seq.tail() == "":
        tail = seq.head().split(".")[-1]
        if tail == "dpx":
            dpx_file = os.path.join(seq.dirname,seq.head())
            print(f"[DEBUG] _get_resolution() - Processing DPX file (no tail): {dpx_file}")
            dpx = _safe_open_dpx(dpx_file)
            if dpx is None:
                print(f"[DEBUG] _get_resolution() END - DPX open failed, returning empty")
                return ""
            try:
                width = dpx.raw_header.OrientHeader.XOriginalSize
                height = dpx.raw_header.OrientHeader.YOriginalSize
                if width == 0:
                    from subprocess import check_output
                    dpx_info = check_output(["rez-env", "oiio","--","iinfo",dpx_file])
                    resolution_info = re.search("\d+\ x\ \d+",dpx_info)
                    if resolution_info :
                        width,height = resolution_info.group().split("x")
                        width = int(width)
                        height = int(height)
                result = '%d x %d'%(width,height)
                print(f"[DEBUG] _get_resolution() END - DPX (no tail) result: {result}")
                return result
            except Exception as e:
                print(f"ERROR: Failed to read resolution from {dpx_file}: {e}")
                print(f"[DEBUG] _get_resolution() END - DPX (no tail) exception, returning empty")
                return ""
        elif tail == "exr":
            exr_file = os.path.join(seq.dirname,seq.head())
            print(f"[DEBUG] _get_resolution() - Processing EXR file (no tail): {exr_file}")
            exr = _safe_open_exr(exr_file)
            if exr is None:
                print(f"[DEBUG] _get_resolution() END - EXR open failed, returning empty")
                return ""
            try:
                if "dataWindow" in exr.header():
                    res = exr.header()['dataWindow']
                    result = "%d x %d"%(res.max.x+1,res.max.y+1)
                    print(f"[DEBUG] _get_resolution() END - EXR (no tail) result: {result}")
                    return result
            except Exception as e:
                print(f"ERROR: Failed to read resolution from {exr_file}: {e}")
            print(f"[DEBUG] _get_resolution() END - EXR (no tail) no dataWindow, returning empty")
            return ""
    else:
        print(f"[DEBUG] _get_resolution() END - Unknown type, returning empty")
        return ""


def _get_sequences(path):
    
    sequences = []

    for temp in os.listdir(path):
        if temp in ['.thumbnail']:
            continue
        temp = os.path.join(path,temp)
        if os.path.isdir(temp):
            sequence = pyseq.get_sequences(temp)
            if sequence:
                sequences.extend(sequence)
    

    return sequences

def _get_movs(path):
    
    movs = []

    mov_files = glob.glob(os.path.join(path,"*.mov"))
    mxf_files =  glob.glob(os.path.join(path,"*.mxf"))
    if mxf_files:
        mov_files.extend(mxf_files)

    
    for mov_file in mov_files:
        
        video_stream = MOV_INFO.video_stream(mov_file)
        mov_info = MOV_INFO(mov_file,video_stream)
        mov_name = mov_file.split(".")[0]
        edl_files = glob.glob(mov_name + "*.edl")
        print(edl_files)
        if edl_files:
            for edl_file in edl_files:
                if os.path.exists(edl_file):
                    parser = Parser(round(mov_info.framerate()))
                    f = open(edl_file)
                    dl = parser.parse(f)
                    first_start = dl[0]
                    for event in dl:

                        cutitem = CutItem()
                        cutitem.clibname = event.clip_name
                        cutitem.start_tc = event.src_start_tc
                        cutitem.end_tc = event.src_end_tc
                        cutitem.rec_start_tc = event.rec_start_tc
                        cutitem.rec_end_tc = event.rec_end_tc
                        mov_info = MOV_INFO(mov_file,video_stream,event,first_start,event.clip_name,cutitem)
                        movs.append(mov_info)    
                    f.close()
        else:
            mov_info = MOV_INFO(mov_file,video_stream)
            movs.append(mov_info)    

    return movs

 




class ExcelWriteModel:

    def __init__( self, excel_path ):

        self._excel_path = excel_path
        self.excel_file  = self._get_excel_file()

        self.wWorkbook  = xlsxwriter.Workbook( self._excel_file )
        self.wWorksheet = self.wWorkbook.add_worksheet()     # 엑셀 파일 생성
        self.bold       = self.wWorkbook.add_format( {'bold': 1} )
        #self.initHorizontalItems()
    
    def _get_excel_file(self):

        excel_files = ""
        excel_files = glob.glob("%s/scanlist_*.xls"%self._excel_path)
        if not excel_files:
            self._excel_file  = "%s/scanlist_01.xls"%self._excel_path
        else:
            last = sorted(excel_files)[-1]
            num = list(filter(str.isdigit,str(os.path.basename(last))))[0]
            new_name = "scanlist_%02d.xls"%(int(num)+1)
            self._excel_file = "%s/%s"%(self._excel_path,new_name)

    @classmethod    
    def get_last_excel_file(self,path):
        excel_files = ""
        excel_files = glob.glob("%s/scanlist_*.xls"%path)
        if not excel_files:
            return None
        else:
            last = sorted(excel_files)[-1]
            return last
    
    @classmethod    
    def read_excel(self,excel_file):


        rWorkbook  = xlrd.open_workbook( excel_file )
        rWorksheet = rWorkbook.sheet_by_name( 'Sheet1' )
        rows = rWorksheet.nrows  
        cols = rWorksheet.ncols
        array = []
        for row in range(1,rows):
            info = []
            check_data = rWorksheet.cell_value( row, MODEL_KEYS['check'] )
            check_box = QtGui.QCheckBox()
            if check_data:
                check_box.setChecked(True)
            info.append(check_box)
            for col in range(1,cols):
                data = rWorksheet.cell_value( row, col )
                if not data == "NaN":
                    if col == 1:
                        ext = rWorksheet.cell_value(row,MODEL_KEYS['ext'])
                        if ext in ['mov']:
                            path = rWorksheet.cell_value( row, 7 )
                        else:
                            path = os.path.dirname(rWorksheet.cell_value( row, 7 ))
                        thumbnail_path = os.path.join(path,
                            ".thumbnail")
                        thumbnail_file = os.path.join(thumbnail_path,data)
                        info.append(thumbnail_file)
                    elif col in [MODEL_KEYS["timecode_in"],MODEL_KEYS['timecode_out']]:
                        if type(data) == float:
                            data = "%08d"%int(data)
                            temp = list(data)
                            temp = [ temp[x]+temp[x+1] for x in range(0,len(temp)) if (x+1)%2 == 1 ]
                            data = ":".join(temp)
                        info.append(data)
                    else:
                        info.append(data)
                else:
                    info.append("")
            array.append(info)
        return array
    
    def write_model_to_excel(self,model):
        for col in range(0,len(model.header)):

            self.wWorksheet.write(0,col,model.header[col])

        for row in range(0,model.rowCount(None)):
            index = model.createIndex(row,MODEL_KEYS['check'])
            check_box = model.data(index,QtCore.Qt.CheckStateRole)
            if check_box:
                self.wWorksheet.write( row+1, MODEL_KEYS['check'], "o" )

            for col in range(1,model.columnCount(None)):
                index = model.createIndex(row,col)
                data = model.data(index,QtCore.Qt.DisplayRole )
                try:
                    if data == "" :
                        self.wWorksheet.write( row+1, col, "" )
                    else:
                        if col == 1:
                            thumbnail_file = os.path.basename(data)
                            self.wWorksheet.write( row+1, col, thumbnail_file )
                        else:
                            self.wWorksheet.write( row+1, col, data )
                    if col == 1:
                        #col = self.wWorksheet.col(1)
                        #col.width = 240
                        self.wWorksheet.set_row( row+1, 144 )   # 엑셀 높이설정 (썸네일크기 맞춰서)
                        self.wWorksheet.insert_image( row+1, col,data,{'x_scale':0.25, 'y_scale': 0.25})

                except Exception as e :
                    print(e)
                    pass
        
        for col in list(MODEL_KEYS.values())[1:]:
            self.wWorksheet.set_column( col,col ,15 )
        self.wWorksheet.set_column( MODEL_KEYS['thumbnail'], MODEL_KEYS['thumbnail'], 40 )
        self.wWorksheet.set_column( MODEL_KEYS['scan_path'], MODEL_KEYS['scan_path'], 45 )
        self.wWorkbook.close()

    def set_global_data( self ,temp_folder,scan_date ):
        self.ws_2 = self.wWorkbook.add_worksheet()
        self.ws_2.write( 0 , 0 , temp_folder )
        self.ws_2.write( 1 , 0 , self.excelfile )
        self.ws_2.write( 2 , 0 , scan_date )

    def initHorizontalItems( self ):
        for i, col in enumerate( HORIZONTALITEMS ):
            self.wWorksheet.write( string.uppercase[i] + '1', col[0], self.bold ) ### A1(0행 0열에 col값)
            self.wWorksheet.set_column( '{0}:{0}'.format( string.uppercase[i]), col[1] ) ### ( Colum 넓이 조정 )
            self.bold.set_align( 'center')
            self.bold.set_align( 'vcenter')
            self.bold.set_bg_color( 'green')
            self.bold.set_font_size ( 13 )

    def saveExcel( self ):
        self.wWorkbook.close()
        if os.path.isfile( self.excelfile ):
            return True
        else :
            return False

    def insertImage( self, row, col, img ):
        ''' 엑셀 이미지 넣기 (썸네일)'''
        if not os.path.isfile( img ):
            pass
        else:
            col_size,rowsize = Image.open(img).size
            #self.wWorksheet.set_column( col, col, 20 )
            self.wWorksheet.set_row( row, 60 )   # 엑셀 높이설정 (썸네일크기 맞춰서)
            self.wWorksheet.insert_image( row, col, img, {'x_scale': 0.00001, 'y_scale': 0.00001} )

    def insertData( self, row, col, string ):
        self.wWorksheet.write( row, col, string )

    def insertDataN( self, row, colName, string ):
        #col = HORIZONTALITEMS.index( colName )
        self.wWorksheet.write( row, colName, string )


def get_time_code(dir_name,head,frame_format,frame,tail):

    if tail == "mov":

        mov_file = os.path.join(dir_name,head)
        video_stream = MOV_INFO.video_stream(mov_file)
        mov_info = MOV_INFO(mov_file,video_stream)
        start_timecode = mov_info.video_stream['tags']['timecode']
        n ,d = mov_info.video_stream['r_frame_rate'].split("/")
        frame_rate = float(n) / float(d)
        start_timecode = Timecode(round(frame_rate),str(start_timecode))
        return str(start_timecode + (int(frame) - 1))

    if tail == "exr":
        exr_file = os.path.join(dir_name,head+"."+frame_format%frame+"."+tail)
        exr = _safe_open_exr(exr_file)
        if exr is None:
            return ""
        try:
            if "timeCode" in exr.header():
                ti = exr.header()['timeCode']
                return "%02d:%02d:%02d:%02d"%(ti.hours,ti.minutes,ti.seconds,ti.frame)
        except Exception as e:
            print(f"ERROR: Failed to read timecode from {exr_file}: {e}")
        return ""
    elif tail == "dpx":
        dpx_file = os.path.join(dir_name,head+"."+frame_format%frame+"."+tail)
        dpx = _safe_open_dpx(dpx_file)
        if dpx is None:
            return ""
        try:
            return dpx.tv_header.time_code
        except Exception as e:
            print(f"ERROR: Failed to read timecode from {dpx_file}: {e}")
            return ""
    else:
        return ""

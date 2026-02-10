# :coding: utf-8

import os
from config.app_config import Context


class ShotgunCommands(object):
    """
    Shotgun 명령어 헬퍼 클래스

    Sequence, Shot, PublishedFile 등을 생성하고 관리합니다.
    """

    def __init__(self, app, sg, project, clip_project, user, context):
        """
        Args:
            app: 앱 인스턴스 (독립 모드) 또는 SGTK 앱 (호환 모드)
            sg: Shotgun API 인스턴스
            project: 프로젝트 엔티티
            clip_project: 클립 프로젝트 엔티티
            user: 사용자 엔티티
            context: Context 인스턴스
        """
        self._app = app
        self._sg = sg
        self._project = project
        self._clip_project = clip_project
        self._user = user
        self._context = context
        self._clip_tag = []

    def create_seq(self, seq_name):
        project = self._project
        if seq_name == 'clip':
            project = self._clip_project

        key = [
               ['project', 'is', project],
               ['code', 'is', seq_name]
              ]

        seq_ent = self._sg.find_one('Sequence', key)
        if seq_ent:
            self.seq_ent = seq_ent
            return self.seq_ent
        desc = {
                'project': project,
                'code': seq_name
               }
        self.seq_ent = self._sg.create("Sequence", desc)
        return self.seq_ent

    def get_tags(self, tag_name):
        for tag in tag_name:
            filters = [['name', 'is', tag]]
            fields = ['type', 'id', 'name']
            tag_info = self._sg.find_one('Tag', filters, fields)
            if not tag_info:
                tag_dict = {'name': tag}
                self._sg.create('Tag', tag_dict)

            self._clip_tag.append(tag_info)
        return self._clip_tag

    def create_shot(self, shot_name):
        """Shot을 생성하거나 기존 Shot을 반환합니다."""
        print("create Shot")  # Python 3 호환
        project = self._project
        if 'src' in shot_name:
            project = self._clip_project

        key = [
               ['project', 'is', project],
               ['sg_sequence', 'is', self.seq_ent],
               ['code', 'is', shot_name]
              ]

        shot_ent = self._sg.find_one('Shot', key)
        if 'src' in shot_name:
            fields = ['code', 'tags']
            shot_ent = self._sg.find_one('Shot', key, fields)

        if shot_ent:
            # Python 3 호환: .keys() 제거, in 사용
            if 'src' not in shot_name or 'tags' in shot_ent:
                self.shot_ent = shot_ent
                return self.shot_ent

        desc = {
                'project': project,
                'sg_sequence': self.seq_ent,
                'code': shot_name,
                'tags': []
               }
        if 'src' in shot_name:
            desc['tags'] += self._clip_tag
        self.shot_ent = self._sg.create("Shot", desc)
        return self.shot_ent

    def publish_temp_jpg(self, data_fields):
        """
        임시 JPG 파일을 Shotgun에 PublishedFile로 등록합니다.

        Args:
            data_fields: [plate_path, plate_file_name, version, file_type]

        Returns:
            tuple: (published_entity, status) - status는 'OLD' 또는 'NEW'
        """
        plate_path = data_fields[0]
        plate_file_name = data_fields[1]
        version = data_fields[2]
        file_type = data_fields[3]

        temp_jpg_dir = plate_path.split('/')[:-1]
        temp_jpg_path = os.path.join('/'.join(temp_jpg_dir), "v%03d_jpg" % (version + 1))
        file_name = plate_file_name.replace('v%03d' % version, 'v%03d' % (version + 1))
        published_file = os.path.join(temp_jpg_path, file_name + ".%04d.jpg")
        published_name = os.path.basename(published_file)

        key = [
               ['project', 'is', self._project],
               ['entity', 'is', self.shot_ent],
               ["published_file_type", "is", file_type],
               ['name', 'is', published_name],
               ['version_number', 'is', int(version)]
              ]
        self.published_tmp_ent = self._sg.find_one("PublishedFile", key, ['version_number'])

        if self.published_tmp_ent:
            return (self.published_tmp_ent, 'OLD')

        # sgtk.util.register_publish 대신 직접 Shotgun API 사용
        publish_data = {
            "project": self._project,
            "entity": self.shot_ent,
            "code": published_name,
            "name": published_name,
            "path": {"local_path": published_file},
            "published_file_type": {"type": "PublishedFileType", "name": "Plate"},
            "version_number": version,
            "created_by": self._user,
        }

        self.published_tmp_ent = self._sg.create("PublishedFile", publish_data)
        return (self.published_tmp_ent, 'NEW')

    def publish_to_shotgun(self, data_fields):
        """
        파일을 Shotgun에 PublishedFile로 등록합니다.

        Args:
            data_fields: [version, published_file_type, version_file_name, seq_type, published_file]

        Returns:
            tuple: (published_entity, status) - status는 'OLD', 'NEW', 또는 None
        """
        version = data_fields[0]
        published_file_type = data_fields[1]
        version_file_name = data_fields[2]
        seq_type = data_fields[3]
        published_file = data_fields[4]

        key = [
               ['project', 'is', self._project],
               ['entity', 'is', self.shot_ent],
               ["published_file_type", "is", published_file_type],
               ['name', 'is', version_file_name],
               ['version_number', 'is', int(version)]
              ]
        self.published_ent = self._sg.find_one("PublishedFile", key, ['version_number'])

        if self.published_ent:
            return (self.published_ent, 'OLD')

        # Published file type 결정
        if seq_type == "org":
            published_type = "Plate"
        elif seq_type == "ref":
            published_type = "Reference"
        else:
            published_type = "Source"

        if published_file is None:
            return ({}, None)

        # sgtk.util.register_publish 대신 직접 Shotgun API 사용
        publish_data = {
            "project": self._project,
            "entity": self.shot_ent,
            "code": version_file_name,
            "name": version_file_name,
            "path": {"local_path": published_file},
            "published_file_type": {"type": "PublishedFileType", "name": published_type},
            "version_number": version,
            "created_by": self._user,
        }

        self.published_ent = self._sg.create("PublishedFile", publish_data)
        return (self.published_ent, 'NEW')
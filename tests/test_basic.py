# -*- coding: utf-8 -*-
"""
立体声转5.1&7.1声道混音工具 - 基础测试
v3.0.0 by 陈迹启行
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestProjectStructure:
    """测试项目结构完整性"""
    
    def test_main_py_exists(self):
        """测试 main.py 是否存在"""
        assert os.path.exists('main.py'), "main.py 文件不存在"
    
    def test_web_mixer_exists(self):
        """测试 web_mixer.py 是否存在"""
        assert os.path.exists('web_mixer.py'), "web_mixer.py 文件不存在"
    
    def test_requirements_exists(self):
        """测试 requirements.txt 是否存在"""
        assert os.path.exists('requirements.txt'), "requirements.txt 文件不存在"
    
    def test_web_templates_exist(self):
        """测试 Web 模板文件是否存在"""
        assert os.path.exists('web_templates/setup.html'), "setup.html 不存在"
        assert os.path.exists('web_templates/mixer.html'), "mixer.html 不存在"
    
    def test_logic_bsroformer_exists(self):
        """测试音频分离模块是否存在"""
        assert os.path.exists('logic_bsroformer/inference.py'), "inference.py 不存在"
        assert os.path.exists('logic_bsroformer/configs'), "configs 目录不存在"


class TestPythonSyntax:
    """测试 Python 语法正确性"""
    
    def test_main_py_syntax(self):
        """测试 main.py 语法"""
        try:
            with open('main.py', 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, 'main.py', 'exec')
        except SyntaxError as e:
            pytest.fail(f"main.py 语法错误: {e}")
    
    def test_web_mixer_syntax(self):
        """测试 web_mixer.py 语法"""
        try:
            with open('web_mixer.py', 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, 'web_mixer.py', 'exec')
        except SyntaxError as e:
            pytest.fail(f"web_mixer.py 语法错误: {e}")


class TestVersionInfo:
    """测试版本信息"""
    
    def test_version_in_main(self):
        """测试 main.py 中的版本号"""
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'v3.0.0' in content or '3.0.0' in content, "版本号应为 v3.0.0"
    
    def test_author_info(self):
        """测试作者信息"""
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        assert '陈迹启行' in content, "作者信息应为 陈迹启行"


class TestHTMLTemplates:
    """测试 HTML 模板"""
    
    def test_setup_html_structure(self):
        """测试 setup.html 基本结构"""
        with open('web_templates/setup.html', 'r', encoding='utf-8') as f:
            content = f.read()
        assert '<!DOCTYPE html>' in content, "缺少 DOCTYPE 声明"
        assert '<html' in content, "缺少 html 标签"
        assert '</html>' in content, "缺少 html 结束标签"
    
    def test_mixer_html_structure(self):
        """测试 mixer.html 基本结构"""
        with open('web_templates/mixer.html', 'r', encoding='utf-8') as f:
            content = f.read()
        assert '<!DOCTYPE html>' in content, "缺少 DOCTYPE 声明"
        assert '<html' in content, "缺少 html 标签"
        assert '</html>' in content, "缺少 html 结束标签"
    
    def test_mixer_has_channel_selector(self):
        """测试 mixer.html 是否包含声道选择器"""
        with open('web_templates/mixer.html', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'channelModeSelect' in content, "缺少声道选择器"


class TestDependencies:
    """测试依赖项"""
    
    def test_flask_importable(self):
        """测试 Flask 是否可导入"""
        try:
            import flask
        except ImportError:
            pytest.skip("Flask 未安装")
    
    def test_pydub_importable(self):
        """测试 PyDub 是否可导入"""
        try:
            import pydub
        except ImportError:
            pytest.skip("PyDub 未安装")
    
    def test_numpy_importable(self):
        """测试 NumPy 是否可导入"""
        try:
            import numpy
        except ImportError:
            pytest.skip("NumPy 未安装")


class TestConfigFiles:
    """测试配置文件"""
    
    def test_model_config_exists(self):
        """测试模型配置文件是否存在"""
        config_path = 'logic_bsroformer/configs/logic_pro_config_v1.yaml'
        assert os.path.exists(config_path), f"配置文件不存在: {config_path}"
    
    def test_requirements_not_empty(self):
        """测试 requirements.txt 不为空"""
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read().strip()
        assert len(content) > 0, "requirements.txt 不应为空"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

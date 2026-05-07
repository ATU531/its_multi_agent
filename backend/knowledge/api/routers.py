import os.path
import logging
import shutil

import aiofiles

from config.settings import settings

logging.basicConfig(level=logging.DEBUG)
logger=logging.getLogger(__name__)
from fastapi import APIRouter,UploadFile,File,HTTPException
from fastapi.concurrency import run_in_threadpool
from services.ingestion.ingestion_processor import IngestionProcessor
from  schemas.schema import UploadResponse

import  tempfile
# 1.创建APIRouter
router=APIRouter()
# 2. 创建应用的实例
ingestion_processor=IngestionProcessor()
# IO(对文件读写) 执行SQL 网络请求 典型耗时任务
@router.post("/upload",response_model=UploadResponse,summary="处理知识库上传")
async def  upload_file(file: UploadFile=File(...)):
    # "0430-联想手机K900常见问题汇总.md"

    try:
        # 0.临时目录
        temp_md_dir =settings.TMP_MD_FOLDER_PATH
        file_suffix=os.path.splitext(file.filename)[1]
        tmp_md_path=os.path.join(temp_md_dir,file.filename)
        if not os.path.exists(tmp_md_path):
            os.makedirs(temp_md_dir,exist_ok=True)


        temp_file_path=""
        # 1. 处理临时文件
        async with aiofiles.tempfile.NamedTemporaryFile(delete=False,suffix=file_suffix) as temp_file:

            # a. 读取上传文件的内容 # 对象（异步协程）缓冲区【1M】空间
            while content:=await file.read(1024*1024):
                # b. 将读取到上传文件的内容写入到临时文件
                await temp_file.write(content)

            # c. 获取临时文件的路径 # C:\Users\Administrator\AppData\Local\Temp\tmpe1puxhk7
            temp_file_path=temp_file.name
        shutil.move(temp_file_path, tmp_md_path)

        # 2. 磁盘写入完成,入库操作  # TODO(去重)
        chunks_added= await run_in_threadpool(ingestion_processor.ingest_file,tmp_md_path)
        print(f"临时文件路径:{temp_file_path}")

        # 3.构建文件上传的响应对象
        return UploadResponse(
            status="success",
            message="文档上传知识库成功",
            file_name=file.filename,
            chunks_added=chunks_added
        )

    except Exception as e:
            raise HTTPException(status_code=500,detail=f"文件上传到知识库失败:{str(e)}")

    finally:
        # 4. 清空临时文件路径(磁盘空间不足)
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"临时文件:{temp_file_path}已删除...")































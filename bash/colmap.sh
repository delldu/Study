#/************************************************************************************
#***
#***	Copyright 2022 Dell(18588220928@163.com), All Rights Reserved.
#***
#***	File Author: Dell, 2022年 05月 30日 星期一 14:13:11 CST
#***
#************************************************************************************/
#
#! /bin/sh

usage()
{
	echo "Usage: $0 dir_name"

	exit 1
}

[ "$1" == "" ] && usage

scene_dir=$1
logfile=$scene_dir/logfile.txt

# Suppose scene_dir has sub dir which is named images

# 1) Feature extractor
colmap feature_extractor \
	--database_path $scene_dir/database.db \
	--image_path $scene_dir/images \
	--ImageReader.single_camera 1 \
	| tee $logfile

    # --SiftExtraction.use_gpu 0

# 2) exhaustive_matcher, sequential_matcher
colmap exhaustive_matcher \
	--database_path $scene_dir/database.db \
	| tee --append $logfile

# # 3) Sparse mapping
# PS: if colmap version >= 3.6, please use '--output_path' instead of following '--export_path'
mkdir -p $scene_dir/sparse
colmap mapper \
	--database_path $scene_dir/database.db \
	--image_path $scene_dir/images \
	--export_path $scene_dir/sparse \
	--Mapper.num_threads 16 \
	--Mapper.init_min_tri_angle 4 \
	--Mapper.multiple_models 0 \
	--Mapper.extract_colors 0 \
	| tee --append $logfile

colmap model_converter \
	--input_path $scene_dir/sparse/0 \
	--output_path $scene_dir/sparse/0 \
	--output_type TXT \
 	| tee --append $logfile

# 4) Dense restruction
# mkdir $scene_dir/dense
# colmap image_undistorter \
#     --image_path $scene_dir/images \
#     --input_path $scene_dir/sparse/0 \
#     --output_path $scene_dir/dense \
#     --output_type COLMAP \
#     --max_image_size 2000 \
# 	| tee --append $logfile

# 5) Geometric fusion
# colmap dense_stereo \
#     --workspace_path $scene_dir/dense \
#     --workspace_format COLMAP \
# 	--DenseStereo.max_image_size 2000 \
#     --PatchMatchStereo.geom_consistency true \
#  	| tee --append $logfile

# colmap dense_fuser \
#     --workspace_path $scene_dir/dense \
#     --workspace_format COLMAP \
#     --input_type geometric \
#     --output_path $scene_dir/dense/g-fused.ply \
# 	| tee --append $logfile

# colmap dense_mesher \
#     --input_path $scene_dir/dense/g-fused.ply \
#     --output_path $scene_dir/dense/g-meshed.ply \
# 	| tee --append $logfile


# 6) Photometric fusion
# colmap dense_stereo \
# 	--workspace_path $scene_dir/dense \
# 	--workspace_format COLMAP \
# 	--DenseStereo.max_image_size 2000 \
# 	--DenseStereo.geom_consistency false \
# | tee --append $logfile

# colmap dense_fuser \
# 	--workspace_path $scene_dir/dense \
#   --workspace_format COLMAP \
#   --input_type photometric \
#   --output_path $scene_dir/dense/p-fused.ply \
# | tee --append $logfile

# colmap dense_mesher \
#   --input_path $scene_dir/dense/p-fused.ply \
#   --output_path $scene_dir/dense/p-meshed.ply \
# | tee --append $logfile

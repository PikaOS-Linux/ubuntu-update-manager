# Clone Upstream
mkdir -p ./pkg-pika/update-manager
rsync -av ./* ./pkg-pika/update-manager/ --exclude=pkg-pika
cd ./pkg-pika/update-manager
# Get build deps
apt-get build-dep ./ -y

# Build package
dpkg-buildpackage --no-sign

# Move the debs to output
cd ../
mkdir -p ../output
mv ./*.deb ../output/

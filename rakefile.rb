require 'yaml'
require 'rubygems'

desc 'Build and send to dev server'
task :build do
    jekyll
    
    puts 'Done.'
end

def jekyll
  puts 'Building Jekyll pages...'
  sh 'bundle exec jekyll build --trace'
  puts 'Jekyll page build complete.'
end

task :deploy do
    deployToDev
end

task :push do
    deployToLive
end

def deployToDev
    puts 'Sending to server...'
    sh 'rsync -avz --exclude=wwwscot --delete _site/ david@dev-lamp.local:/home/wwwroot/dwi/'
    puts 'Sent'

end

def deployToLive
    puts 'Pushing to live...'
    currentTime = Time.now.strftime("%d/%m/%Y %H:%M")
    sh 'rm -rf ./wwwscot'
    sh 'rm -rf _site/wwwscot'
    sh 'rhc git-clone -a wwwscot'
    sh 'cp -R _site/* wwwscot/'
    sh "cd wwwscot && git add . && git commit -m 'New build #{currentTime}' && git push"
end

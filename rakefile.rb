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
    upload
end

def upload
    puts 'Sending to server...'
    sh 'rsync -avz --delete _site/ david@dev-lamp.local:/home/wwwroot/dwi/'
    puts 'Sent'

end

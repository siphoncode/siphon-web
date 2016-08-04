module.exports = function(grunt) {
  // Configuration
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    // Task config
    browserify: {
      dev: {
        src: './static/js/dashboard/**/*.js',
        dest: './static/js/dashboard-bundle.js',
        options: {
          transform: ['babelify'],
          watch: true,
          keepAlive: true,
          watchifyOptions: {
            poll: false
          }
        }
      },
      production: {
        src: './static/js/dashboard/**/*.js',
        dest: './.static/js/dashboard-bundle.js',
        options: {
          transform: ['babelify']
        }
      }
    },
    uglify: {
      build: {
        src: './.static/js/dashboard-bundle.js',
        dest: './.static/js/dashboard-bundle.js'
      }
    }
  });

  // Load plugins
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-browserify');

  // Register tasks
  grunt.registerTask('default', ['browserify:dev']);
  grunt.registerTask('production', ['browserify:production', 'uglify']);
};

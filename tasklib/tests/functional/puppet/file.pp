file { "test" :
  path    => "/tmp/test",
  ensure  => present,
  mode    => 0640,
  content => "I'm a file created created by tasklib test",
}
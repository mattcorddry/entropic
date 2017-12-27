#!/usr/bin/perl
#
# export iTunes playlists to M3U files, one per playlist
#
# mattcorddry | 2017-12-27
#

use strict;
use warnings;

use Data::Dumper;
use Getopt::Long;
use Mac::iTunes::Library;
use Mac::iTunes::Library::XML;
use Mac::iTunes::Library::Playlist;
use URI::Encode qw(uri_encode uri_decode);

# defaults
die "No HOME set!" unless $ENV{'HOME'};
my $itunes_lib = $ENV{'HOME'} . "/Music/iTunes/iTunes Music Library.xml";
my $export_dir = $ENV{'HOME'} . "/Music/Export";

# regex of allowed file extensions in playlists, all others will be skipped
my $allowed_files_r = qr{\.(mp3|m4a|wav)$};
my $allowed_dir_r = qr{^$ENV{'HOME'}/Music/iTunes/iTunes Media/Music};

# strip this path from the front of all files
my $path_strip = "$ENV{'HOME'}/Music/iTunes/iTunes Media/Music";

#
# read the iTunes library
#
# $lib = read_itunes_library($xml_file);
sub read_itunes_library {
    my $xmlfile = shift;

    my $lib = Mac::iTunes::Library::XML->parse($xmlfile)
        or die "Failed to open $xmlfile: $!\n";

    return $lib;
}

#
# write one M3U file, does not mangle paths
# https://en.wikipedia.org/wiki/M3U
#
# $count = write_m3u($filename, @$filelist);
sub write_m3u {
    my $m3ufile = shift;
    my $list = shift;

    die "No file list present" unless ref($list) eq 'ARRAY';

    open (my $fh, ">", $m3ufile)
        or die "Could not create $m3ufile: $!\n";

    # mandatory header
    print $fh "#EXTM3U\n";

    my $i = 0;
    foreach my $f (sort @$list) {
        print $fh $f . "\n";
        $i++;
    }

    close $fh
        or die "Unable to write to $m3ufile: $!\n";

    return $i;
}

#
# build a list all playlists, hash by ID to Name
#
# $%list = list_playlists($lib);
sub list_playlists {
    my $lib = shift;

    my %pl = $lib->playlists();
    #print Dumper(\%pl);
    my %list;
    foreach my $p (keys %pl) {
        # skip dynamic playlists
        next if defined($pl{$p}->{'Smart Criteria'});
        next unless $pl{$p}->{'Name'} =~ /\w+/;

        $list{$p} = $pl{$p}->{'Name'};
    }

    die "No playlists found!" unless scalar(keys %list) > 0;
    return \%list;
}

#
# extract files for a single playlist
# $@files = list_files($lib, $playlist);
sub list_files {
    my $lib = shift;
    my $playlist = shift;

    # list of item objects
    my %playlists = $lib->playlists();
    my $items = $playlists{$playlist}->{'items'};
    die "No items found for playlist $playlist" unless (ref($items) eq 'ARRAY');

    # now build a simple filename list
    my @files;
    foreach my $i (@$items) {
        my $u = uri_decode($i->{'Location'});
        if ($u =~ /file:\/\/(.*)$/) {
            my $path = $1;

            # sanity checks
            next unless ($path =~ /$allowed_dir_r/);
            next unless (-f $path);

            if ($path =~ m/$allowed_files_r/i) {
                $path =~ s/^$path_strip//;
                (my $rslash_path = $path) =~ s/\//\\/g;
                push @files, $rslash_path;
            }

        } elsif ($u =~ /http(s?):\/\//) {
            # silently skip web urls
            next;
        } else {
            warn "   ! Unhandled item location $u in playlist $playlist\n";
        }
    }

    # return file list if we got any...
    if (scalar(@files) > 0) {
        return \@files;
    } else {
        warn "   ! No valid files found in playlist $playlist\n";
        return;
    }
}

#
# main control flow
#

# parse CLI options
my $library = $itunes_lib;
my $export = $export_dir;
GetOptions("library=s" => \$library,
           "export=s"  => \$export,
           );

print "iTunes Playlist Exporter\n";
if ( -f $library ) {
    print "-- Source: $library\n";
} else {
    die "Error: $library not found\n";
}
if ( -d $export ) {
    print "-- Destination: $export\n";
} else {
    die "Error: $export not found or not a directory\n";
}

my $lib = read_itunes_library($library);
print "-- Parsed source\n";
# print Dumper($lib);

my $playlists = list_playlists($lib);
print "-- Found " . scalar(keys %$playlists) . " playlists\n";
# print Dumper($playlists);

foreach my $p (%$playlists) {
    next unless $playlists->{$p};
    print "-- Playlist: $playlists->{$p}\n";

    my $files = list_files($lib, $p);
    next unless $files;
    print "   - found " . scalar(@$files) . " valid files\n";

    # generate a filename for the M3U
    my $shortn = $playlists->{$p};
    $shortn =~ s/[[:punct:]]//g;
    $shortn =~ s/\s+/_/g;
    my $m3ufile = $export . "/" . $shortn . ".m3u";

    # write the file
    write_m3u($m3ufile, $files);
    print "   - wrote $m3ufile\n";
}

package com.example.brand.locationsdatabase;

/**
 * Created by brand on 2/21/2018.
 */

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.provider.BaseColumns;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.CursorAdapter;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.SimpleCursorAdapter;
import android.widget.TextView;

import android.app.Activity;
import android.app.Dialog;
import android.content.pm.PackageManager;
import android.location.Location;
import android.support.annotation.NonNull;
import android.support.annotation.Nullable;
import android.support.v4.app.ActivityCompat;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.TextView;

import com.google.android.gms.common.ConnectionResult;
import com.google.android.gms.common.GoogleApiAvailability;
import com.google.android.gms.common.api.GoogleApiClient;
import com.google.android.gms.location.LocationListener;
import com.google.android.gms.location.LocationRequest;
import com.google.android.gms.location.LocationServices;

import static com.google.android.gms.common.GooglePlayServicesUtil.getErrorDialog;

public class LocationActivity extends AppCompatActivity implements GoogleApiClient.ConnectionCallbacks, GoogleApiClient.OnConnectionFailedListener {

    //variables taken from lecture
    //https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
    private GoogleApiClient mGoogleApiClient;
    private LocationRequest mLocationRequest;
    //used string instead of textview in order to add the string of latitude and longitutde
    //https://developer.android.com/reference/java/lang/String.html
    String mLatText;
    String mLonText;
    private Location mLastLocation;
    private LocationListener mLocationListener;
    private static final int LOCATION_PERMISSON_RESULT = 17;

    //variables taken from the week 7 example code files
    //https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
    SQLiteExample mSQLiteExample;
    Button mSQLSubmitButton;
    Cursor mSQLCursor;
    SimpleCursorAdapter mSQLCursorAdapter;
    private static final String TAG = "SQLActivity";
    SQLiteDatabase mSQLDB;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_location);

        if (mGoogleApiClient == null) {
            mGoogleApiClient = new GoogleApiClient.Builder(this)
                    .addConnectionCallbacks(this)
                    .addOnConnectionFailedListener(this)
                    .addApi(LocationServices.API)
                    .build();
        }

        //taken from the example code file
        //https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
        //Added the longitude and latitude along with the denied location requirements
        mLocationRequest = LocationRequest.create();
        mLocationRequest.setPriority(LocationRequest.PRIORITY_HIGH_ACCURACY);
        //Decreased the internvals in order to refresh the location faster
        mLocationRequest.setInterval(10);
        mLocationRequest.setFastestInterval(10);
        mLocationListener = new LocationListener() {
            @Override
            public void onLocationChanged(Location location) {
                if (location != null) {
                    mLonText = "  Longitude: " + String.valueOf(location.getLongitude());
                    mLatText = "Latitude: " + String.valueOf(location.getLatitude());
                } else {
                    mLonText = "  Longitude: -123.2 ";
                    mLatText = "Latitude: 44.5";
                }
            }
        };

        //taken from the week 7 example code files
        //https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
        mSQLiteExample = new SQLiteExample(this);
        mSQLDB = mSQLiteExample.getWritableDatabase();

        mSQLSubmitButton = (Button) findViewById(R.id.sql_add_row_button);
        mSQLSubmitButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if(mSQLDB != null){
                    ContentValues vals = new ContentValues();
                    vals.put(DBContract.DemoTable.COLUMN_NAME_DEMO_STRING, ((EditText)findViewById(R.id.sql_text_input)).getText().toString());
                    updateLocation(); // checks for permission and updates mLatText + mLonText
                    vals.put(DBContract.DemoTable.COLUMN_NAME_DEMO_INT, mLatText + mLonText);
                    mSQLDB.insert(DBContract.DemoTable.TABLE_NAME,null,vals);
                    populateTable();
                } else {
                    Log.d(TAG, "Unable to access database for writing.");
                }
            }
        });

        populateTable();
    }

    //taken from the example code file
    //https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
    @Override
    protected void onStart() {
        mGoogleApiClient.connect();
        super.onStart();
    }

    //taken from the example code file
    //https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
    @Override
    protected void onStop() {
        mGoogleApiClient.disconnect();
        super.onStop();
    }

    //taken from the example code file
    //https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
    //code in the database also sets the longitude and latitude if the permission was denied
    @Override
    public void onConnected(@Nullable Bundle bundle) {
        if (ActivityCompat.checkSelfPermission(this,
                android.Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED &&
                ActivityCompat.checkSelfPermission(this, android.Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{android.Manifest.permission.ACCESS_FINE_LOCATION, android.Manifest.permission.ACCESS_COARSE_LOCATION}, LOCATION_PERMISSON_RESULT);
            mLonText = "  Longitude: -123.2 ";
            mLatText = "Latitude: 44.5";
            return;
        }
        updateLocation();
    }

    //taken from the example code file
    //https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
    @Override
    public void onConnectionSuspended(int i) {

    }

    //taken from the example code file
    //https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
    @Override
    public void onConnectionFailed(@NonNull ConnectionResult connectionResult) {
        Dialog errDialog = GoogleApiAvailability.getInstance().getErrorDialog(this, connectionResult.getErrorCode(), 0);
        errDialog.show();
        return;
    }

    //taken from the example code file
    //https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults){
        if(requestCode == LOCATION_PERMISSON_RESULT){
            if(grantResults.length > 0){
                updateLocation();
            }
        }
    }

    //Adapted the update location() from lecture to instead of calling the FusedLocationApi again it would output the OSU location stated in the requirements
    //https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
    private void updateLocation() {
        if (ActivityCompat.checkSelfPermission(this, android.Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED && ActivityCompat.checkSelfPermission(this, android.Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            return;
        }
        mLastLocation = LocationServices.FusedLocationApi.getLastLocation(mGoogleApiClient);

        if(mLastLocation != null){
            mLonText = "Longitude: " + mLastLocation.getLongitude();
            mLatText = "  Latitude: " + mLastLocation.getLatitude();
        }
        else {
            mLonText = "Longitude: -123.2 ";
            mLatText = "  Latitude: 44.5";
        }
    }
    //taken from the week 7 example code files
    //https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
    private void populateTable(){
        if(mSQLDB != null) {
            try {
                if(mSQLCursorAdapter != null && mSQLCursorAdapter.getCursor() != null){
                    if(!mSQLCursorAdapter.getCursor().isClosed()){
                        mSQLCursorAdapter.getCursor().close();
                    }
                }
                mSQLCursor = mSQLDB.query(DBContract.DemoTable.TABLE_NAME,
                        new String[]{DBContract.DemoTable._ID, DBContract.DemoTable.COLUMN_NAME_DEMO_STRING,
                                DBContract.DemoTable.COLUMN_NAME_DEMO_INT}, null, null, null, null, null);
                ListView SQLListView = (ListView) findViewById(R.id.sql_list_view);
                mSQLCursorAdapter = new SimpleCursorAdapter(this,
                        R.layout.sql_item,
                        mSQLCursor,
                        new String[]{DBContract.DemoTable.COLUMN_NAME_DEMO_STRING, DBContract.DemoTable.COLUMN_NAME_DEMO_INT},
                        new int[]{R.id.sql_listview_string, R.id.sql_listview_int},
                        0);
                SQLListView.setAdapter(mSQLCursorAdapter);
            } catch (Exception e) {
                Log.d(TAG, "Error loading data from database");
            }
        }
    }
}

//taken from the week 7 example code files
//https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
class SQLiteExample extends SQLiteOpenHelper {

    public SQLiteExample(Context context) {
        super(context, DBContract.DemoTable.DB_NAME, null, DBContract.DemoTable.DB_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL(DBContract.DemoTable.SQL_CREATE_DEMO_TABLE);
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        db.execSQL(DBContract.DemoTable.SQL_DROP_DEMO_TABLE);
        onCreate(db);
    }
}

//taken from the week 7 example code files
//https://gist.github.com/wolfordj/4017cbedfd755a805bb3124958b08ec2
final class DBContract {
    private DBContract(){};

    public final class DemoTable implements BaseColumns {
        public static final String DB_NAME = "demo_db";
        public static final String TABLE_NAME = "demo";
        public static final String COLUMN_NAME_DEMO_STRING = "demo_string";
        public static final String COLUMN_NAME_DEMO_INT = "demo_int";
        public static final int DB_VERSION = 32;


        public static final String SQL_CREATE_DEMO_TABLE = "CREATE TABLE " +
                DemoTable.TABLE_NAME + "(" + DemoTable._ID + " INTEGER PRIMARY KEY NOT NULL," +
                DemoTable.COLUMN_NAME_DEMO_STRING + " VARCHAR(255)," +
                DemoTable.COLUMN_NAME_DEMO_INT + " INTEGER);";

        public  static final String SQL_DROP_DEMO_TABLE = "DROP TABLE IF EXISTS " + DemoTable.TABLE_NAME;
    }
}



